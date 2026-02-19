"""
Unit tests for The Mind card game.
"""

import unittest
from the_mind import TheMind, GameState


class TestTheMindGame(unittest.TestCase):
    """Test cases for The Mind game."""
    
    def test_game_initialization(self):
        """Test game initializes with correct values."""
        game = TheMind(num_players=2)
        self.assertEqual(game.num_players, 2)
        self.assertEqual(game.current_level, 1)
        self.assertEqual(game.lives, 2)
        self.assertEqual(game.throwing_stars, 1)
        self.assertEqual(game.state, GameState.SETUP)
    
    def test_invalid_player_count(self):
        """Test that invalid player counts raise an error."""
        with self.assertRaises(ValueError):
            TheMind(num_players=1)
        with self.assertRaises(ValueError):
            TheMind(num_players=5)
    
    def test_level_setup(self):
        """Test that level setup deals correct number of cards."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Each player should have cards equal to current level
        self.assertEqual(len(game.get_player_hand(0)), game.current_level)
        self.assertEqual(len(game.get_player_hand(1)), game.current_level)
        self.assertEqual(game.state, GameState.IN_PROGRESS)
    
    def test_play_card_in_order(self):
        """Test playing cards in correct order."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Manually set up a simple scenario
        game.player_hands = {0: [10, 50], 1: [20, 60]}
        game.played_pile = []
        
        # Play cards in order
        success, msg = game.play_card(0, 10)
        self.assertTrue(success)
        self.assertEqual(game.played_pile, [10])
        
        success, msg = game.play_card(1, 20)
        self.assertTrue(success)
        self.assertEqual(game.played_pile, [10, 20])
    
    def test_play_card_out_of_order(self):
        """Test that playing out of order loses a life."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Set up scenario where playing out of order will occur
        game.player_hands = {0: [30], 1: [20]}
        game.played_pile = []
        initial_lives = game.lives
        
        # Play 30 first
        success, msg = game.play_card(0, 30)
        self.assertTrue(success)
        
        # Try to play 20 (should fail)
        success, msg = game.play_card(1, 20)
        self.assertFalse(success)
        self.assertEqual(game.lives, initial_lives - 1)
    
    def test_throwing_star(self):
        """Test using throwing star to discard lowest cards."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        game.player_hands = {0: [10, 50], 1: [20, 60]}
        initial_stars = game.throwing_stars
        
        success, discarded = game.use_throwing_star()
        self.assertTrue(success)
        self.assertEqual(game.throwing_stars, initial_stars - 1)
        self.assertEqual(discarded[0], 10)
        self.assertEqual(discarded[1], 20)
        self.assertEqual(game.player_hands[0], [50])
        self.assertEqual(game.player_hands[1], [60])
    
    def test_level_completion(self):
        """Test that level completes when all cards are played."""
        game = TheMind(num_players=2)
        game.current_level = 1
        game.setup_level()
        
        # Set up simple scenario
        game.player_hands = {0: [10], 1: [20]}
        game.played_pile = []
        
        # Play all cards
        game.play_card(0, 10)
        game.play_card(1, 20)
        
        self.assertEqual(game.state, GameState.LEVEL_COMPLETE)
        self.assertEqual(game.current_level, 2)
    
    def test_game_won(self):
        """Test that game is won after completing all 12 levels."""
        game = TheMind(num_players=2)
        game.current_level = 12
        game.setup_level()
        
        # Set up to complete level 12
        game.player_hands = {0: [], 1: []}
        game.state = GameState.IN_PROGRESS
        
        # Trigger level completion check
        game._complete_level()
        
        self.assertEqual(game.state, GameState.GAME_WON)
    
    def test_game_lost(self):
        """Test that game is lost when lives reach 0."""
        game = TheMind(num_players=2)
        game.setup_level()
        game.lives = 1
        
        # Set up scenario to lose last life
        game.player_hands = {0: [5], 1: [30]}
        game.played_pile = [10]
        
        # Play card out of order (5 < 10)
        game.play_card(0, 5)
        
        self.assertEqual(game.lives, 0)
        self.assertEqual(game.state, GameState.GAME_LOST)
    
    def test_get_game_info(self):
        """Test that game info returns correct data."""
        game = TheMind(num_players=3)
        game.setup_level()
        
        info = game.get_game_info()
        self.assertEqual(info["num_players"], 3)
        self.assertEqual(info["current_level"], 1)
        self.assertEqual(info["lives"], 3)
        self.assertEqual(info["throwing_stars"], 1)
        self.assertIn("state", info)
        self.assertIn("played_pile", info)


if __name__ == "__main__":
    unittest.main()
