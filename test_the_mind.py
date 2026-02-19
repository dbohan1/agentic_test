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
    
    def test_skipped_cards_loses_life(self):
        """Test that playing a card higher than another player's card loses a life."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Player 0 has 50, Player 1 has 20
        game.player_hands = {0: [50], 1: [20]}
        game.played_pile = []
        initial_lives = game.lives
        
        # Player 0 plays 50, skipping Player 1's 20
        success, msg = game.play_card(0, 50)
        self.assertTrue(success)
        self.assertEqual(game.lives, initial_lives - 1)
        self.assertIn("skipped", msg)
        # Player 1's card 20 should be discarded
        self.assertEqual(game.player_hands[1], [])
        self.assertIn(20, game.discarded_cards)
    
    def test_skipped_cards_multiple_players(self):
        """Test skipped cards across multiple players."""
        game = TheMind(num_players=3)
        game.setup_level()
        
        # Player 0 has 60, Player 1 has 20, Player 2 has 40
        game.player_hands = {0: [60], 1: [20], 2: [40]}
        game.played_pile = []
        initial_lives = game.lives
        
        # Player 0 plays 60, skipping cards 20 and 40
        success, msg = game.play_card(0, 60)
        self.assertTrue(success)
        self.assertEqual(game.lives, initial_lives - 1)
        self.assertEqual(game.player_hands[1], [])
        self.assertEqual(game.player_hands[2], [])
        self.assertIn(20, game.discarded_cards)
        self.assertIn(40, game.discarded_cards)
    
    def test_no_skipped_cards_no_life_loss(self):
        """Test that playing the lowest available card does not lose a life."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Player 0 has 10, Player 1 has 50
        game.player_hands = {0: [10], 1: [50]}
        game.played_pile = []
        initial_lives = game.lives
        
        # Player 0 plays 10 (no cards lower than 10 exist)
        success, msg = game.play_card(0, 10)
        self.assertTrue(success)
        self.assertEqual(game.lives, initial_lives)
        self.assertNotIn("skipped", msg)
    
    def test_skipped_cards_own_hand(self):
        """Test that a player's own lower cards are also discarded."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Player 0 has 10 and 50, Player 1 has 60
        game.player_hands = {0: [10, 50], 1: [60]}
        game.played_pile = []
        initial_lives = game.lives
        
        # Player 0 plays 50, their own 10 should be skipped
        success, msg = game.play_card(0, 50)
        self.assertTrue(success)
        self.assertEqual(game.lives, initial_lives - 1)
        self.assertEqual(game.player_hands[0], [])
        self.assertIn(10, game.discarded_cards)
    
    def test_skipped_cards_game_over(self):
        """Test that skipped cards can cause game over."""
        game = TheMind(num_players=2)
        game.setup_level()
        game.lives = 1
        
        # Player 0 has 50, Player 1 has 20
        game.player_hands = {0: [50], 1: [20]}
        game.played_pile = []
        
        # Player 0 plays 50, skipping Player 1's 20
        success, msg = game.play_card(0, 50)
        self.assertTrue(success)
        self.assertEqual(game.lives, 0)
        self.assertEqual(game.state, GameState.GAME_LOST)
    
    def test_skipped_cards_with_pile_context(self):
        """Test that only cards between last played and played card are skipped."""
        game = TheMind(num_players=2)
        game.setup_level()
        
        # Pile already has card 30
        game.player_hands = {0: [50], 1: [25, 40]}
        game.played_pile = [30]
        initial_lives = game.lives
        
        # Player 0 plays 50. Player 1's 40 is between 30 and 50 (skipped).
        # Player 1's 25 is NOT between 30 and 50 (not skipped).
        success, msg = game.play_card(0, 50)
        self.assertTrue(success)
        self.assertEqual(game.lives, initial_lives - 1)
        self.assertIn(40, game.discarded_cards)
        self.assertNotIn(25, game.discarded_cards)
        self.assertEqual(game.player_hands[1], [25])


if __name__ == "__main__":
    unittest.main()
