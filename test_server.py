"""
Unit tests for The Mind WebSocket server.
"""

import unittest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from server import GameServer, GameRoom
from the_mind import GameState


class TestGameRoom(unittest.TestCase):
    """Test cases for the GameRoom class."""

    def test_room_creation(self):
        """Test game room initializes correctly."""
        room = GameRoom("test-room", 2)
        self.assertEqual(room.room_id, "test-room")
        self.assertEqual(room.num_players, 2)
        self.assertFalse(room.is_full)
        self.assertIsNone(room.game)
        self.assertEqual(room.game_type, "the_mind")

    def test_room_creation_with_game_type(self):
        """Test game room initializes with custom game type."""
        room = GameRoom("test-room", 3, game_type="ore_wood_offer_letters")
        self.assertEqual(room.game_type, "ore_wood_offer_letters")
        self.assertEqual(room.num_players, 3)

    def test_add_player(self):
        """Test adding players to a room."""
        room = GameRoom("test", 2)
        ws1 = MagicMock()
        ws2 = MagicMock()

        pid0 = room.add_player("Alice", ws1)
        self.assertEqual(pid0, 0)
        self.assertFalse(room.is_full)

        pid1 = room.add_player("Bob", ws2)
        self.assertEqual(pid1, 1)
        self.assertTrue(room.is_full)

    def test_remove_player(self):
        """Test removing a player from a room."""
        room = GameRoom("test", 2)
        ws = MagicMock()
        room.add_player("Alice", ws)
        room.remove_player(0)
        self.assertEqual(len(room.players), 0)

    def test_get_player_id(self):
        """Test looking up player ID by WebSocket."""
        room = GameRoom("test", 2)
        ws1 = MagicMock()
        ws2 = MagicMock()
        room.add_player("Alice", ws1)
        room.add_player("Bob", ws2)

        self.assertEqual(room.get_player_id(ws1), 0)
        self.assertEqual(room.get_player_id(ws2), 1)
        self.assertIsNone(room.get_player_id(MagicMock()))


class TestGameServer(unittest.TestCase):
    """Test cases for the GameServer class."""

    def setUp(self):
        self.server = GameServer()

    def test_create_room(self):
        """Test creating a game room."""
        room = self.server.create_room("room1", 2)
        self.assertIsNotNone(room)
        self.assertEqual(room.room_id, "room1")
        self.assertEqual(room.game_type, "the_mind")
        self.assertIn("room1", self.server.rooms)

    def test_create_room_with_game_type(self):
        """Test creating a room with a specific game type."""
        room = self.server.create_room("room1", 2, game_type="ore_wood_offer_letters")
        self.assertEqual(room.game_type, "ore_wood_offer_letters")

    def test_create_duplicate_room(self):
        """Test creating a room with a duplicate ID raises error."""
        self.server.create_room("room1", 2)
        with self.assertRaises(ValueError):
            self.server.create_room("room1", 3)

    def test_create_room_invalid_players(self):
        """Test creating a room with invalid player count."""
        with self.assertRaises(ValueError):
            self.server.create_room("room1", 5)
        with self.assertRaises(ValueError):
            self.server.create_room("room1", 1)

    def test_get_room(self):
        """Test retrieving a room."""
        self.server.create_room("room1", 2)
        self.assertIsNotNone(self.server.get_room("room1"))
        self.assertIsNone(self.server.get_room("nonexistent"))

    def test_remove_room(self):
        """Test removing a room."""
        self.server.create_room("room1", 2)
        self.server.remove_room("room1")
        self.assertNotIn("room1", self.server.rooms)


class TestGameServerAsync(unittest.TestCase):
    """Async test cases for message handling."""

    def setUp(self):
        self.server = GameServer()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def _make_ws(self):
        ws = AsyncMock()
        ws.send = AsyncMock()
        return ws

    def test_handle_create_room(self):
        """Test creating a room via WebSocket message."""
        ws = self._make_ws()
        msg = json.dumps({
            "action": "create_room",
            "room_id": "game1",
            "num_players": 2,
            "name": "Alice"
        })
        self._run(self.server.handle_message(ws, msg))

        ws.send.assert_called_once()
        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "room_joined")
        self.assertEqual(response["room_id"], "game1")
        self.assertEqual(response["player_id"], 0)
        self.assertEqual(response["game_type"], "the_mind")

    def test_handle_create_room_with_game_type(self):
        """Test creating a room with game_type via WebSocket message."""
        ws = self._make_ws()
        msg = json.dumps({
            "action": "create_room",
            "room_id": "game1",
            "num_players": 2,
            "name": "Alice",
            "game_type": "ore_wood_offer_letters"
        })
        self._run(self.server.handle_message(ws, msg))

        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "room_joined")
        self.assertEqual(response["game_type"], "ore_wood_offer_letters")

    def test_handle_list_rooms_includes_game_type(self):
        """Test that room list includes game_type."""
        ws = self._make_ws()
        self.server.create_room("room1", 2, "the_mind")
        self.server.create_room("room2", 3, "ore_wood_offer_letters")

        self._run(self.server.handle_message(ws, json.dumps({"action": "list_rooms"})))

        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "room_list")
        self.assertEqual(len(response["rooms"]), 2)
        game_types = {r["room_id"]: r["game_type"] for r in response["rooms"]}
        self.assertEqual(game_types["room1"], "the_mind")
        self.assertEqual(game_types["room2"], "ore_wood_offer_letters")

    def test_handle_join_room(self):
        """Test joining a room via WebSocket message."""
        ws1 = self._make_ws()
        ws2 = self._make_ws()

        # Create room
        self._run(self.server.handle_message(ws1, json.dumps({
            "action": "create_room", "room_id": "game1", "num_players": 2, "name": "Alice"
        })))

        # Join room
        self._run(self.server.handle_message(ws2, json.dumps({
            "action": "join_room", "room_id": "game1", "name": "Bob"
        })))

        # Should have received room_joined + player_joined + game_started + game_state
        self.assertTrue(ws2.send.call_count >= 2)

    def test_handle_join_nonexistent_room(self):
        """Test joining a room that doesn't exist."""
        ws = self._make_ws()
        self._run(self.server.handle_message(ws, json.dumps({
            "action": "join_room", "room_id": "nope", "name": "Alice"
        })))

        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "error")

    def test_handle_play_card(self):
        """Test playing a card via WebSocket message."""
        ws1 = self._make_ws()
        ws2 = self._make_ws()

        # Create and fill room
        self._run(self.server.handle_message(ws1, json.dumps({
            "action": "create_room", "room_id": "game1", "num_players": 2, "name": "Alice"
        })))
        self._run(self.server.handle_message(ws2, json.dumps({
            "action": "join_room", "room_id": "game1", "name": "Bob"
        })))

        # Set up known hands
        room = self.server.get_room("game1")
        room.game.player_hands = {0: [10], 1: [20]}
        room.game.played_pile = []

        # Play a card
        ws1.send.reset_mock()
        self._run(self.server.handle_message(ws1, json.dumps({
            "action": "play_card", "card": 10
        })))

        # Player 1 should have received messages
        self.assertTrue(ws1.send.call_count >= 1)

    def test_handle_list_rooms(self):
        """Test listing rooms via WebSocket message."""
        ws = self._make_ws()
        self.server.create_room("room1", 2)

        self._run(self.server.handle_message(ws, json.dumps({"action": "list_rooms"})))

        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "room_list")
        self.assertEqual(len(response["rooms"]), 1)
        self.assertEqual(response["rooms"][0]["room_id"], "room1")

    def test_handle_invalid_json(self):
        """Test handling invalid JSON input."""
        ws = self._make_ws()
        self._run(self.server.handle_message(ws, "not json"))

        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "error")

    def test_handle_unknown_action(self):
        """Test handling unknown action."""
        ws = self._make_ws()
        self._run(self.server.handle_message(ws, json.dumps({"action": "fly"})))

        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "error")

    def test_handle_disconnect(self):
        """Test handling player disconnect."""
        ws1 = self._make_ws()
        ws2 = self._make_ws()

        # Create and join a room
        self._run(self.server.handle_message(ws1, json.dumps({
            "action": "create_room", "room_id": "game1", "num_players": 3, "name": "Alice"
        })))
        self._run(self.server.handle_message(ws2, json.dumps({
            "action": "join_room", "room_id": "game1", "name": "Bob"
        })))

        # Disconnect ws1
        self._run(self.server.handle_disconnect(ws1))
        room = self.server.get_room("game1")
        self.assertIsNotNone(room)
        self.assertEqual(len(room.players), 1)

        # Disconnect ws2 - room should be removed
        self._run(self.server.handle_disconnect(ws2))
        self.assertIsNone(self.server.get_room("game1"))

    def test_handle_create_room_empty_id(self):
        """Test creating a room with empty ID."""
        ws = self._make_ws()
        self._run(self.server.handle_message(ws, json.dumps({
            "action": "create_room", "room_id": "", "num_players": 2, "name": "Alice"
        })))
        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "error")

    def test_handle_join_full_room(self):
        """Test joining a full room."""
        ws1 = self._make_ws()
        ws2 = self._make_ws()
        ws3 = self._make_ws()

        self._run(self.server.handle_message(ws1, json.dumps({
            "action": "create_room", "room_id": "game1", "num_players": 2, "name": "Alice"
        })))
        self._run(self.server.handle_message(ws2, json.dumps({
            "action": "join_room", "room_id": "game1", "name": "Bob"
        })))
        self._run(self.server.handle_message(ws3, json.dumps({
            "action": "join_room", "room_id": "game1", "name": "Charlie"
        })))

        response = json.loads(ws3.send.call_args[0][0])
        self.assertEqual(response["type"], "error")
        self.assertIn("full", response["message"])


class TestAzrokServerAsync(unittest.TestCase):
    """Async test cases for Azrok's Republic WebSocket handling."""

    def setUp(self):
        self.server = GameServer()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def _run(self, coro):
        return self.loop.run_until_complete(coro)

    def _make_ws(self):
        ws = AsyncMock()
        ws.send = AsyncMock()
        return ws

    def _create_full_azrok_room(self):
        """Create a room with 4 players and auto-start the game."""
        players = [self._make_ws() for _ in range(4)]
        self._run(self.server.handle_message(players[0], json.dumps({
            "action": "create_room", "room_id": "azrok1", "num_players": 4,
            "name": "Alice", "game_type": "azroks_republic"
        })))
        for i, name in enumerate(["Bob", "Charlie", "Diana"], start=1):
            self._run(self.server.handle_message(players[i], json.dumps({
                "action": "join_room", "room_id": "azrok1", "name": name
            })))
        return players

    def test_create_azrok_room(self):
        """Test creating an Azrok's Republic room via WebSocket."""
        ws = self._make_ws()
        self._run(self.server.handle_message(ws, json.dumps({
            "action": "create_room", "room_id": "azrok1", "num_players": 4,
            "name": "Alice", "game_type": "azroks_republic"
        })))
        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "room_joined")
        self.assertEqual(response["game_type"], "azroks_republic")

    def test_azrok_game_starts_with_4_players(self):
        """Test that Azrok's Republic game starts when 4 players join."""
        players = self._create_full_azrok_room()
        room = self.server.get_room("azrok1")
        self.assertIsNotNone(room.game)
        self.assertEqual(room.game_type, "azroks_republic")

    def test_azrok_game_state_includes_role(self):
        """Test that game state includes player role info."""
        players = self._create_full_azrok_room()
        # Find a game_state message sent to player 0
        for call in players[0].send.call_args_list:
            msg = json.loads(call[0][0])
            if msg.get("type") == "game_state" and "your_role" in msg:
                self.assertIn(msg["your_role"], [
                    "Brother of the Republic", "Agent of the Drow"
                ])
                self.assertIn("your_sector", msg)
                self.assertIn("your_money", msg)
                self.assertIn("your_id", msg)
                return
        self.fail("No game_state with role info found")

    def test_azrok_invest_people(self):
        """Test investing in people via WebSocket."""
        players = self._create_full_azrok_room()
        room = self.server.get_room("azrok1")
        current = room.game.get_current_player()
        ws = players[current]
        ws.send.reset_mock()

        self._run(self.server.handle_message(ws, json.dumps({
            "action": "invest_people", "amount": 1
        })))
        # Should receive action_result + game_state
        found_result = False
        for call in ws.send.call_args_list:
            msg = json.loads(call[0][0])
            if msg.get("type") == "action_result" and msg.get("action") == "invest_people":
                self.assertTrue(msg["success"])
                found_result = True
        self.assertTrue(found_result)

    def test_azrok_end_turn(self):
        """Test ending a turn via WebSocket."""
        players = self._create_full_azrok_room()
        room = self.server.get_room("azrok1")
        current = room.game.get_current_player()
        ws = players[current]
        ws.send.reset_mock()

        self._run(self.server.handle_message(ws, json.dumps({
            "action": "end_turn"
        })))
        found_result = False
        for call in ws.send.call_args_list:
            msg = json.loads(call[0][0])
            if msg.get("type") == "action_result" and msg.get("action") == "end_turn":
                self.assertTrue(msg["success"])
                found_result = True
        self.assertTrue(found_result)

    def test_azrok_resolve_and_next_round(self):
        """Test resolving a round and starting next round via WebSocket."""
        players = self._create_full_azrok_room()
        room = self.server.get_room("azrok1")

        # End all 4 turns to reach resolution
        for _ in range(4):
            current = room.game.get_current_player()
            self._run(self.server.handle_message(players[current], json.dumps({
                "action": "end_turn"
            })))

        from azroks_republic import AzrokGameState
        self.assertEqual(room.game.state, AzrokGameState.RESOLUTION_PHASE)

        # Resolve round
        ws = players[0]
        ws.send.reset_mock()
        self._run(self.server.handle_message(ws, json.dumps({
            "action": "resolve_round"
        })))
        found = False
        for call in ws.send.call_args_list:
            msg = json.loads(call[0][0])
            if msg.get("type") == "action_result" and msg.get("action") == "resolve_round":
                self.assertTrue(msg["result"]["success"])
                found = True
        self.assertTrue(found)

        self.assertEqual(room.game.state, AzrokGameState.ROUND_END)

        # Start next round
        ws.send.reset_mock()
        self._run(self.server.handle_message(ws, json.dumps({
            "action": "start_round"
        })))
        found = False
        for call in ws.send.call_args_list:
            msg = json.loads(call[0][0])
            if msg.get("type") == "action_result" and msg.get("action") == "start_round":
                self.assertTrue(msg["result"]["success"])
                found = True
        self.assertTrue(found)

    def test_azrok_invest_people_missing_amount(self):
        """Test invest_people without amount returns error."""
        players = self._create_full_azrok_room()
        room = self.server.get_room("azrok1")
        current = room.game.get_current_player()
        ws = players[current]
        ws.send.reset_mock()

        self._run(self.server.handle_message(ws, json.dumps({
            "action": "invest_people"
        })))
        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "error")
        self.assertIn("Amount", response["message"])

    def test_azrok_use_tax_missing_target(self):
        """Test use_tax without target_id returns error."""
        players = self._create_full_azrok_room()
        room = self.server.get_room("azrok1")
        current = room.game.get_current_player()
        ws = players[current]
        ws.send.reset_mock()

        self._run(self.server.handle_message(ws, json.dumps({
            "action": "use_tax"
        })))
        response = json.loads(ws.send.call_args[0][0])
        self.assertEqual(response["type"], "error")
        self.assertIn("Target", response["message"])


if __name__ == "__main__":
    unittest.main()
