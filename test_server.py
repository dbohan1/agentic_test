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
        self.assertIn("room1", self.server.rooms)

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


if __name__ == "__main__":
    unittest.main()
