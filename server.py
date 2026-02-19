"""
WebSocket server for Happy Hour Games platform.

Manages game lobbies, player connections, and relays game state
to connected clients via WebSocket messages.
"""

import asyncio
import json
import os
from typing import Dict, Optional, Set, Union

import websockets
from websockets.asyncio.server import ServerConnection
from websockets.datastructures import Headers
from websockets.http11 import Request, Response

from the_mind import TheMind, GameState
from azroks_republic import AzroksRepublic, AzrokGameState
from team_supreme_scribbles import TeamSupremeScribbles, ScribblesGameState


class GameRoom:
    """Represents a game room where players connect and play."""

    def __init__(self, room_id: str, num_players: int, game_type: str = "the_mind"):
        self.room_id = room_id
        self.num_players = num_players
        self.game_type = game_type
        self.players: Dict[int, ServerConnection] = {}
        self.player_names: Dict[int, str] = {}
        self.game: Optional[Union[TheMind, AzroksRepublic, TeamSupremeScribbles]] = None

    @property
    def is_full(self) -> bool:
        return len(self.players) >= self.num_players

    def add_player(self, name: str, ws: ServerConnection) -> int:
        """Add a player and return their player_id."""
        player_id = len(self.players)
        self.players[player_id] = ws
        self.player_names[player_id] = name
        return player_id

    def remove_player(self, player_id: int) -> None:
        """Remove a player from the room."""
        self.players.pop(player_id, None)
        self.player_names.pop(player_id, None)

    def get_player_id(self, ws: ServerConnection) -> Optional[int]:
        """Find the player_id for a given WebSocket connection."""
        for pid, conn in self.players.items():
            if conn is ws:
                return pid
        return None


class GameServer:
    """Manages game rooms and WebSocket connections."""

    def __init__(self):
        self.rooms: Dict[str, GameRoom] = {}
        self.connection_room: Dict[ServerConnection, str] = {}

    def create_room(self, room_id: str, num_players: int, game_type: str = "the_mind") -> GameRoom:
        """Create a new game room."""
        if room_id in self.rooms:
            raise ValueError(f"Room '{room_id}' already exists")
        if game_type == "team_supreme_scribbles":
            if num_players < 1:
                raise ValueError("Number of players must be at least 1")
        else:
            if not 2 <= num_players <= 4:
                raise ValueError("Number of players must be 2-4")
        room = GameRoom(room_id, num_players, game_type)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Optional[GameRoom]:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str) -> None:
        self.rooms.pop(room_id, None)

    async def broadcast(self, room: GameRoom, message: dict) -> None:
        """Send a message to all players in a room."""
        data = json.dumps(message)
        disconnected = []
        for pid, ws in room.players.items():
            try:
                await ws.send(data)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(pid)
        for pid in disconnected:
            room.remove_player(pid)

    async def send_to_player(self, room: GameRoom, player_id: int, message: dict) -> None:
        """Send a message to a specific player."""
        ws = room.players.get(player_id)
        if ws:
            try:
                await ws.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                room.remove_player(player_id)

    def _build_game_state(self, room: GameRoom) -> dict:
        """Build the shared game state for broadcasting."""
        if not room.game:
            return {"type": "game_state", "state": "waiting"}
        info = room.game.get_game_info()
        return {
            "type": "game_state",
            **info,
            "player_names": room.player_names,
        }

    async def send_game_state(self, room: GameRoom) -> None:
        """Send full game state to all players, including individual info."""
        state = self._build_game_state(room)
        for pid in room.players:
            player_state = {**state}
            if room.game:
                if room.game_type == "azroks_republic":
                    pinfo = room.game.get_player_info(pid)
                    player_state["your_role"] = pinfo.get("role")
                    player_state["your_sector"] = pinfo.get("sector")
                    player_state["your_money"] = pinfo.get("money")
                    player_state["your_improvement_level"] = pinfo.get("improvement_level")
                    player_state["your_salary"] = pinfo.get("salary")
                    player_state["your_id"] = pid
                elif room.game_type == "team_supreme_scribbles":
                    player_state["your_id"] = pid
                    if pid == room.game.current_drawer:
                        drawer_info = room.game.get_drawer_info()
                        player_state["your_word"] = drawer_info.get("word")
                else:
                    player_state["your_hand"] = room.game.get_player_hand(pid)
                    player_state["your_id"] = pid
            await self.send_to_player(room, pid, player_state)

    async def handle_message(self, ws: ServerConnection, data: str) -> None:
        """Process an incoming WebSocket message."""
        try:
            msg = json.loads(data)
        except json.JSONDecodeError:
            await ws.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
            return

        action = msg.get("action")
        if action == "create_room":
            await self._handle_create_room(ws, msg)
        elif action == "join_room":
            await self._handle_join_room(ws, msg)
        elif action == "play_card":
            await self._handle_play_card(ws, msg)
        elif action == "use_star":
            await self._handle_use_star(ws)
        elif action == "next_level":
            await self._handle_next_level(ws)
        elif action == "list_rooms":
            await self._handle_list_rooms(ws)
        elif action == "invest_people":
            await self._handle_azrok_action(ws, "invest_people", msg)
        elif action == "invest_improvement":
            await self._handle_azrok_action(ws, "invest_improvement", msg)
        elif action == "use_tax":
            await self._handle_azrok_action(ws, "use_tax", msg)
        elif action == "buy_powder_charge":
            await self._handle_azrok_action(ws, "buy_powder_charge", msg)
        elif action == "buy_azroks_dagger":
            await self._handle_azrok_action(ws, "buy_azroks_dagger", msg)
        elif action == "end_turn":
            await self._handle_azrok_action(ws, "end_turn", msg)
        elif action == "resolve_round":
            await self._handle_azrok_action(ws, "resolve_round", msg)
        elif action in ("start_round", "next_round"):
            await self._handle_azrok_action(ws, "start_round", msg)
        elif action == "scribbles_start_round":
            await self._handle_scribbles_action(ws, "start_round", msg)
        elif action == "scribbles_guess":
            await self._handle_scribbles_action(ws, "guess", msg)
        elif action == "scribbles_end_drawing":
            await self._handle_scribbles_action(ws, "end_drawing", msg)
        elif action == "scribbles_draw":
            await self._handle_scribbles_draw(ws, msg)
        elif action == "scribbles_clear":
            await self._handle_scribbles_clear(ws)
        else:
            await ws.send(json.dumps({"type": "error", "message": f"Unknown action: {action}"}))

    async def _get_room_and_player(
        self, ws: ServerConnection
    ) -> tuple[Optional[GameRoom], Optional[int], Optional[str]]:
        """Helper to get room and player_id for a ws connection.

        Returns (room, player_id, room_id) or (None, None, None) on error.
        """
        room_id = self.connection_room.get(ws)
        if not room_id:
            await ws.send(json.dumps({"type": "error", "message": "Not in a room"}))
            return None, None, None
        room = self.get_room(room_id)
        if not room or not room.game:
            await ws.send(json.dumps({"type": "error", "message": "Game not started"}))
            return None, None, None
        player_id = room.get_player_id(ws)
        if player_id is None:
            await ws.send(json.dumps({"type": "error", "message": "Player not found"}))
            return None, None, None
        return room, player_id, room_id

    async def _handle_azrok_action(self, ws: ServerConnection, action_name: str, msg: dict) -> None:
        """Handle an Azrok's Republic game action."""
        room, player_id, room_id = await self._get_room_and_player(ws)
        if room is None:
            return

        if action_name == "invest_people":
            amount = msg.get("amount")
            if amount is None:
                await ws.send(json.dumps({"type": "error", "message": "Amount required"}))
                return
            success, message = room.game.invest_people(player_id, int(amount))
        elif action_name == "invest_improvement":
            success, message = room.game.invest_improvement(player_id)
        elif action_name == "use_tax":
            target_id = msg.get("target_id")
            if target_id is None:
                await ws.send(json.dumps({"type": "error", "message": "Target ID required"}))
                return
            success, message = room.game.use_tax(player_id, int(target_id))
        elif action_name == "buy_powder_charge":
            success, message = room.game.buy_powder_charge(player_id)
        elif action_name == "buy_azroks_dagger":
            success, message = room.game.buy_azroks_dagger(player_id)
        elif action_name == "end_turn":
            success, message = room.game.end_turn(player_id)
        elif action_name == "resolve_round":
            result = room.game.resolve_round()
            await self.broadcast(room, {
                "type": "action_result",
                "action": "resolve_round",
                "result": result,
            })
            await self.send_game_state(room)
            return
        elif action_name == "start_round":
            result = room.game.start_round()
            await self.broadcast(room, {
                "type": "action_result",
                "action": "start_round",
                "result": result,
            })
            await self.send_game_state(room)
            return
        else:
            await ws.send(json.dumps({"type": "error", "message": f"Unknown azrok action: {action_name}"}))
            return

        await self.broadcast(room, {
            "type": "action_result",
            "action": action_name,
            "player_id": player_id,
            "player_name": room.player_names.get(player_id, ""),
            "success": success,
            "message": message,
        })
        await self.send_game_state(room)

    async def _handle_scribbles_action(self, ws: ServerConnection, action_name: str, msg: dict) -> None:
        """Handle a Team Supreme Scribbles game action."""
        room, player_id, room_id = await self._get_room_and_player(ws)
        if room is None:
            return

        if action_name == "start_round":
            result = room.game.start_round()
            await self.broadcast(room, {
                "type": "action_result",
                "action": "scribbles_start_round",
                "result": result,
            })
            await self.send_game_state(room)
            return
        elif action_name == "guess":
            word = msg.get("word", "")
            if not word:
                await ws.send(json.dumps({"type": "error", "message": "Word is required"}))
                return
            correct, message = room.game.guess(player_id, word)
            await self.broadcast(room, {
                "type": "action_result",
                "action": "scribbles_guess",
                "player_id": player_id,
                "player_name": room.player_names.get(player_id, ""),
                "correct": correct,
                "message": message,
            })
            await self.send_game_state(room)
            return
        elif action_name == "end_drawing":
            success, message = room.game.end_drawing()
            await self.broadcast(room, {
                "type": "action_result",
                "action": "scribbles_end_drawing",
                "success": success,
                "message": message,
            })
            await self.send_game_state(room)
            return

        await ws.send(json.dumps({"type": "error", "message": f"Unknown scribbles action: {action_name}"}))

    async def _handle_scribbles_draw(self, ws: ServerConnection, msg: dict) -> None:
        """Relay drawing data from the drawer to all other players."""
        room, player_id, room_id = await self._get_room_and_player(ws)
        if room is None:
            return

        # Only the current drawer can send draw data
        if player_id != room.game.current_drawer:
            return

        # Relay stroke data to all other players
        stroke = msg.get("stroke")
        if stroke is None:
            return

        data = json.dumps({"type": "scribbles_draw", "stroke": stroke})
        for pid, conn in room.players.items():
            if pid != player_id:
                try:
                    await conn.send(data)
                except websockets.exceptions.ConnectionClosed:
                    pass

    async def _handle_scribbles_clear(self, ws: ServerConnection) -> None:
        """Relay canvas clear from the drawer to all other players."""
        room, player_id, room_id = await self._get_room_and_player(ws)
        if room is None:
            return

        if player_id != room.game.current_drawer:
            return

        data = json.dumps({"type": "scribbles_clear"})
        for pid, conn in room.players.items():
            if pid != player_id:
                try:
                    await conn.send(data)
                except websockets.exceptions.ConnectionClosed:
                    pass

    async def _handle_create_room(self, ws: ServerConnection, msg: dict) -> None:
        room_id = msg.get("room_id", "").strip()
        num_players = msg.get("num_players", 2)
        name = msg.get("name", "Player").strip()
        game_type = msg.get("game_type", "the_mind").strip()

        if not room_id:
            await ws.send(json.dumps({"type": "error", "message": "Room ID is required"}))
            return

        try:
            room = self.create_room(room_id, int(num_players), game_type)
        except ValueError as e:
            await ws.send(json.dumps({"type": "error", "message": str(e)}))
            return

        player_id = room.add_player(name, ws)
        self.connection_room[ws] = room_id

        await ws.send(json.dumps({
            "type": "room_joined",
            "room_id": room_id,
            "player_id": player_id,
            "player_name": name,
            "num_players": room.num_players,
            "current_players": len(room.players),
            "game_type": room.game_type,
        }))

    async def _handle_join_room(self, ws: ServerConnection, msg: dict) -> None:
        room_id = msg.get("room_id", "").strip()
        name = msg.get("name", "Player").strip()

        room = self.get_room(room_id)
        if not room:
            await ws.send(json.dumps({"type": "error", "message": f"Room '{room_id}' not found"}))
            return

        if room.is_full:
            await ws.send(json.dumps({"type": "error", "message": "Room is full"}))
            return

        player_id = room.add_player(name, ws)
        self.connection_room[ws] = room_id

        await ws.send(json.dumps({
            "type": "room_joined",
            "room_id": room_id,
            "player_id": player_id,
            "player_name": name,
            "num_players": room.num_players,
            "current_players": len(room.players),
            "game_type": room.game_type,
        }))

        await self.broadcast(room, {
            "type": "player_joined",
            "player_id": player_id,
            "player_name": name,
            "current_players": len(room.players),
            "num_players": room.num_players,
        })

        # Auto-start game when room is full
        if room.is_full:
            if room.game_type == "azroks_republic":
                game = AzroksRepublic(room.num_players)
                game.setup_game()
                game.start_round()
                room.game = game
            elif room.game_type == "team_supreme_scribbles":
                game = TeamSupremeScribbles(room.num_players)
                game.start_round()
                room.game = game
            else:
                room.game = TheMind(room.num_players)
                room.game.setup_level()
            await self.broadcast(room, {"type": "game_started"})
            await self.send_game_state(room)

    async def _handle_play_card(self, ws: ServerConnection, msg: dict) -> None:
        room_id = self.connection_room.get(ws)
        if not room_id:
            await ws.send(json.dumps({"type": "error", "message": "Not in a room"}))
            return

        room = self.get_room(room_id)
        if not room or not room.game:
            await ws.send(json.dumps({"type": "error", "message": "Game not started"}))
            return

        player_id = room.get_player_id(ws)
        if player_id is None:
            await ws.send(json.dumps({"type": "error", "message": "Player not found"}))
            return

        card = msg.get("card")
        if card is None:
            await ws.send(json.dumps({"type": "error", "message": "Card value required"}))
            return

        success, message = room.game.play_card(player_id, int(card))

        await self.broadcast(room, {
            "type": "card_played",
            "player_id": player_id,
            "player_name": room.player_names.get(player_id, ""),
            "card": int(card),
            "success": success,
            "message": message,
        })

        await self.send_game_state(room)

    async def _handle_use_star(self, ws: ServerConnection) -> None:
        room_id = self.connection_room.get(ws)
        if not room_id:
            return

        room = self.get_room(room_id)
        if not room or not room.game:
            return

        success, discarded = room.game.use_throwing_star()

        discarded_info = {
            str(pid): {"card": card, "name": room.player_names.get(pid, "")}
            for pid, card in discarded.items()
        }

        await self.broadcast(room, {
            "type": "star_used",
            "success": success,
            "discarded": discarded_info,
        })

        await self.send_game_state(room)

    async def _handle_next_level(self, ws: ServerConnection) -> None:
        room_id = self.connection_room.get(ws)
        if not room_id:
            return

        room = self.get_room(room_id)
        if not room or not room.game:
            return

        if room.game.state == GameState.LEVEL_COMPLETE:
            room.game.setup_level()
            await self.broadcast(room, {
                "type": "level_started",
                "level": room.game.current_level,
            })
            await self.send_game_state(room)

    async def _handle_list_rooms(self, ws: ServerConnection) -> None:
        room_list = []
        for rid, room in self.rooms.items():
            room_list.append({
                "room_id": rid,
                "num_players": room.num_players,
                "current_players": len(room.players),
                "in_progress": room.game is not None,
                "game_type": room.game_type,
            })
        await ws.send(json.dumps({"type": "room_list", "rooms": room_list}))

    async def handle_disconnect(self, ws: ServerConnection) -> None:
        """Handle a player disconnecting."""
        room_id = self.connection_room.pop(ws, None)
        if not room_id:
            return

        room = self.get_room(room_id)
        if not room:
            return

        player_id = room.get_player_id(ws)
        if player_id is not None:
            name = room.player_names.get(player_id, "")
            room.remove_player(player_id)

            if not room.players:
                self.remove_room(room_id)
            else:
                await self.broadcast(room, {
                    "type": "player_left",
                    "player_id": player_id,
                    "player_name": name,
                })


# Global server instance
game_server = GameServer()


async def handler(websocket: ServerConnection) -> None:
    """Handle a single WebSocket connection."""
    try:
        async for message in websocket:
            await game_server.handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await game_server.handle_disconnect(websocket)


def serve_static(connection: ServerConnection, request: Request) -> Response | None:
    """Serve static files for the web interface."""
    path = request.path
    if path == "/" or path == "":
        path = "/index.html"

    # Only intercept non-WebSocket requests (no Upgrade header)
    if any(k.lower() == "upgrade" for k in request.headers):
        return None

    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    file_path = os.path.join(static_dir, path.lstrip("/"))

    # Prevent directory traversal
    file_path = os.path.realpath(file_path)
    if not file_path.startswith(os.path.realpath(static_dir)):
        headers = Headers()
        return Response(403, "Forbidden", headers, b"Forbidden")

    if os.path.isfile(file_path):
        content_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".png": "image/png",
            ".ico": "image/x-icon",
        }
        ext = os.path.splitext(file_path)[1]
        content_type = content_types.get(ext, "application/octet-stream")
        with open(file_path, "rb") as f:
            body = f.read()
        headers = Headers([("Content-Type", content_type)])
        return Response(200, "OK", headers, body)

    return None


async def main(host: str = "0.0.0.0", port: int | None = None) -> None:
    """Start the WebSocket server."""
    if port is None:
        port = int(os.environ.get("PORT", 8765))
    print(f"Starting Happy Hour Games server on ws://{host}:{port}")
    print(f"Open http://localhost:{port} in your browser to play!")

    async with websockets.serve(
        handler,
        host,
        port,
        process_request=serve_static,
    ) as server:
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
