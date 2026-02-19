"""
Unit tests for Team Supreme Scribbles game.
"""

import unittest
from team_supreme_scribbles import (
    TeamSupremeScribbles,
    ScribblesGameState,
    WORD_LIST,
)


class TestTeamSupremeScribblesInit(unittest.TestCase):
    """Test cases for game initialization."""

    def test_game_initialization(self):
        """Test game initializes with correct default values."""
        game = TeamSupremeScribbles(num_players=4)
        self.assertEqual(game.num_players, 4)
        self.assertEqual(game.num_rounds, 3)
        self.assertEqual(game.current_round, 0)
        self.assertEqual(game.state, ScribblesGameState.WAITING)
        self.assertIsNone(game.current_word)
        for pid in range(4):
            self.assertEqual(game.scores[pid], 0)

    def test_single_player_allowed(self):
        """Test that a single player game is valid."""
        game = TeamSupremeScribbles(num_players=1)
        self.assertEqual(game.num_players, 1)

    def test_large_player_count_allowed(self):
        """Test that there is no upper player cap."""
        game = TeamSupremeScribbles(num_players=100)
        self.assertEqual(game.num_players, 100)
        self.assertEqual(len(game.scores), 100)

    def test_zero_players_raises_error(self):
        """Test that 0 players raises ValueError."""
        with self.assertRaises(ValueError):
            TeamSupremeScribbles(num_players=0)

    def test_negative_players_raises_error(self):
        """Test that negative player count raises ValueError."""
        with self.assertRaises(ValueError):
            TeamSupremeScribbles(num_players=-1)

    def test_custom_rounds(self):
        """Test custom number of rounds."""
        game = TeamSupremeScribbles(num_players=2, num_rounds=5)
        self.assertEqual(game.num_rounds, 5)


class TestTeamSupremeScribblesWordList(unittest.TestCase):
    """Test cases for the word list."""

    def test_word_list_not_empty(self):
        """Test that the word list has words."""
        self.assertGreater(len(WORD_LIST), 0)

    def test_words_are_strings(self):
        """Test all words are non-empty strings."""
        for word in WORD_LIST:
            self.assertIsInstance(word, str)
            self.assertGreater(len(word.strip()), 0)


class TestTeamSupremeScribblesRounds(unittest.TestCase):
    """Test cases for round mechanics."""

    def test_start_round(self):
        """Test starting the first round."""
        game = TeamSupremeScribbles(num_players=2)
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertEqual(result["round"], 1)
        self.assertEqual(result["drawer"], 0)
        self.assertIn(result["word"], WORD_LIST)
        self.assertEqual(game.state, ScribblesGameState.DRAWING)

    def test_cannot_start_round_while_drawing(self):
        """Test that start_round fails during a drawing round."""
        game = TeamSupremeScribbles(num_players=2)
        game.start_round()
        result = game.start_round()
        self.assertFalse(result["success"])

    def test_drawer_rotates(self):
        """Test that the drawer rotates through players."""
        game = TeamSupremeScribbles(num_players=3, num_rounds=2)
        # Round 1, drawer 0
        result = game.start_round()
        self.assertEqual(result["drawer"], 0)
        game.end_drawing()

        # Round 1, drawer 1
        result = game.start_round()
        self.assertEqual(result["drawer"], 1)
        game.end_drawing()

        # Round 1, drawer 2
        result = game.start_round()
        self.assertEqual(result["drawer"], 2)
        game.end_drawing()

        # Round 2, drawer 0
        result = game.start_round()
        self.assertEqual(result["drawer"], 0)
        self.assertEqual(result["round"], 2)

    def test_game_over_after_all_rounds(self):
        """Test that the game ends after all rounds are played."""
        game = TeamSupremeScribbles(num_players=2, num_rounds=1)
        # Round 1, drawer 0
        game.start_round()
        game.end_drawing()
        # Round 1, drawer 1
        game.start_round()
        game.end_drawing()
        # Should now trigger game over
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertTrue(result.get("game_over"))
        self.assertEqual(game.state, ScribblesGameState.GAME_OVER)

    def test_cannot_start_after_game_over(self):
        """Test that start_round fails when game is over."""
        game = TeamSupremeScribbles(num_players=1, num_rounds=1)
        game.start_round()
        game.end_drawing()
        game.start_round()  # triggers game over
        result = game.start_round()
        self.assertFalse(result["success"])


class TestTeamSupremeScribblesGuessing(unittest.TestCase):
    """Test cases for guessing mechanics."""

    def test_correct_guess(self):
        """Test that a correct guess awards points."""
        game = TeamSupremeScribbles(num_players=3)
        game.start_round()
        word = game.current_word
        correct, msg = game.guess(1, word)
        self.assertTrue(correct)
        self.assertEqual(game.scores[1], 1)  # guesser gets a point
        self.assertEqual(game.scores[0], 1)  # drawer gets a point
        self.assertEqual(game.state, ScribblesGameState.ROUND_END)

    def test_incorrect_guess(self):
        """Test that an incorrect guess does not award points."""
        game = TeamSupremeScribbles(num_players=3)
        game.start_round()
        correct, msg = game.guess(1, "definitely_wrong_answer_xyz")
        self.assertFalse(correct)
        self.assertEqual(game.scores[1], 0)
        self.assertEqual(game.state, ScribblesGameState.DRAWING)

    def test_case_insensitive_guess(self):
        """Test that guessing is case insensitive."""
        game = TeamSupremeScribbles(num_players=2)
        game.start_round()
        word = game.current_word
        correct, msg = game.guess(1, word.upper())
        self.assertTrue(correct)

    def test_drawer_cannot_guess(self):
        """Test that the drawer cannot submit a guess."""
        game = TeamSupremeScribbles(num_players=2)
        game.start_round()
        correct, msg = game.guess(0, game.current_word)
        self.assertFalse(correct)
        self.assertIn("drawer cannot guess", msg)

    def test_guess_not_during_drawing(self):
        """Test that guessing fails when not in drawing state."""
        game = TeamSupremeScribbles(num_players=2)
        correct, msg = game.guess(0, "anything")
        self.assertFalse(correct)
        self.assertIn("No round in progress", msg)

    def test_invalid_player_guess(self):
        """Test that an invalid player ID is rejected."""
        game = TeamSupremeScribbles(num_players=2)
        game.start_round()
        correct, msg = game.guess(99, game.current_word)
        self.assertFalse(correct)
        self.assertIn("Invalid player", msg)


class TestTeamSupremeScribblesEndDrawing(unittest.TestCase):
    """Test cases for ending a drawing round."""

    def test_end_drawing(self):
        """Test ending a drawing round."""
        game = TeamSupremeScribbles(num_players=2)
        game.start_round()
        success, msg = game.end_drawing()
        self.assertTrue(success)
        self.assertEqual(game.state, ScribblesGameState.ROUND_END)

    def test_end_drawing_not_in_progress(self):
        """Test ending drawing when no round is in progress."""
        game = TeamSupremeScribbles(num_players=2)
        success, msg = game.end_drawing()
        self.assertFalse(success)


class TestTeamSupremeScribblesGameInfo(unittest.TestCase):
    """Test cases for game info methods."""

    def test_get_game_info(self):
        """Test get_game_info returns correct data."""
        game = TeamSupremeScribbles(num_players=3)
        game.start_round()
        info = game.get_game_info()
        self.assertEqual(info["num_players"], 3)
        self.assertEqual(info["num_rounds"], 3)
        self.assertEqual(info["current_round"], 1)
        self.assertEqual(info["state"], "drawing")
        self.assertEqual(info["current_drawer"], 0)
        self.assertIn("scores", info)

    def test_get_drawer_info(self):
        """Test get_drawer_info includes the secret word."""
        game = TeamSupremeScribbles(num_players=2)
        game.start_round()
        info = game.get_drawer_info()
        self.assertEqual(info["drawer_id"], 0)
        self.assertIsNotNone(info["word"])

    def test_word_picking_avoids_repeats(self):
        """Test that words are not immediately repeated."""
        game = TeamSupremeScribbles(num_players=2, num_rounds=10)
        words_seen = []
        for _ in range(10):
            game.start_round()
            words_seen.append(game.current_word)
            game.end_drawing()
        # All words picked within 10 turns should be unique
        self.assertEqual(len(words_seen), len(set(words_seen)))


class TestTeamSupremeScribblesFullGame(unittest.TestCase):
    """Integration test for a full game flow."""

    def test_full_game_two_players(self):
        """Test a complete game with two players and 1 round."""
        game = TeamSupremeScribbles(num_players=2, num_rounds=1)

        # Turn 1: player 0 draws, player 1 guesses correctly
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertEqual(result["drawer"], 0)
        word = game.current_word
        correct, _ = game.guess(1, word)
        self.assertTrue(correct)
        self.assertEqual(game.scores[0], 1)
        self.assertEqual(game.scores[1], 1)

        # Turn 2: player 1 draws, player 0 guesses wrong then right
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertEqual(result["drawer"], 1)
        word = game.current_word
        correct, _ = game.guess(0, "wrong answer")
        self.assertFalse(correct)
        correct, _ = game.guess(0, word)
        self.assertTrue(correct)
        self.assertEqual(game.scores[0], 2)
        self.assertEqual(game.scores[1], 2)

        # Game should be over now
        result = game.start_round()
        self.assertTrue(result.get("game_over"))
        self.assertEqual(game.state, ScribblesGameState.GAME_OVER)


if __name__ == "__main__":
    unittest.main()
