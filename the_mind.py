"""
The Mind - A cooperative card game implementation.

Players must work together to play cards in ascending order without 
communicating verbally or through gestures.
"""

import random
from typing import List, Dict, Tuple, TypedDict
from enum import Enum


class GameInfo(TypedDict):
    """Type definition for game information dictionary."""
    num_players: int
    current_level: int
    lives: int
    max_lives: int
    throwing_stars: int
    max_throwing_stars: int
    state: str
    played_pile: List[int]
    cards_in_play: int


class GameState(Enum):
    """Enum representing the state of the game."""
    SETUP = "setup"
    IN_PROGRESS = "in_progress"
    LEVEL_COMPLETE = "level_complete"
    GAME_WON = "game_won"
    GAME_LOST = "game_lost"


class TheMind:
    """
    Main game class for The Mind.
    
    Manages game state, card dealing, and gameplay mechanics.
    """
    
    MAX_LEVELS = 12
    CARD_MIN = 1
    CARD_MAX = 100
    
    # Player count configuration
    # Dictionary maps player_count -> (lives, throwing_stars)
    PLAYER_CONFIG = {
        2: (2, 1),  # 2 players: 2 lives, 1 throwing star
        3: (3, 1),  # 3 players: 3 lives, 1 throwing star
        4: (4, 1),  # 4 players: 4 lives, 1 throwing star
    }
    
    def __init__(self, num_players: int):
        """
        Initialize The Mind game.
        
        Args:
            num_players: Number of players (2-4)
            
        Raises:
            ValueError: If number of players is invalid
        """
        if num_players not in self.PLAYER_CONFIG:
            raise ValueError(f"Invalid number of players. Must be 2-4, got {num_players}")
        
        self.num_players = num_players
        self.current_level = 1
        self.state = GameState.SETUP
        
        # Get lives and throwing stars based on player count
        self.max_lives, self.max_throwing_stars = self.PLAYER_CONFIG[num_players]
        self.lives = self.max_lives
        self.throwing_stars = self.max_throwing_stars
        
        # Initialize deck and hands
        self.deck: List[int] = []
        self.player_hands: Dict[int, List[int]] = {i: [] for i in range(num_players)}
        self.played_pile: List[int] = []
        
        # Track discarded cards (from throwing stars)
        self.discarded_cards: List[int] = []
    
    def setup_level(self) -> None:
        """Set up a new level by shuffling deck and dealing cards."""
        # Create a fresh deck of cards
        self.deck = list(range(self.CARD_MIN, self.CARD_MAX + 1))
        random.shuffle(self.deck)
        
        # Clear previous hands and played pile
        self.player_hands = {i: [] for i in range(self.num_players)}
        self.played_pile = []
        self.discarded_cards = []
        
        # Deal cards to each player (number of cards = current level)
        cards_per_player = self.current_level
        for player_id in range(self.num_players):
            self.player_hands[player_id] = sorted([
                self.deck.pop() for _ in range(cards_per_player)
            ])
        
        self.state = GameState.IN_PROGRESS
    
    def play_card(self, player_id: int, card: int) -> Tuple[bool, str]:
        """
        Attempt to play a card from a player's hand.
        
        Args:
            player_id: ID of the player playing the card
            card: The card value to play
            
        Returns:
            Tuple of (success, message)
        """
        if self.state != GameState.IN_PROGRESS:
            return False, "Game is not in progress"
        
        if player_id not in self.player_hands:
            return False, "Invalid player ID"
        
        if card not in self.player_hands[player_id]:
            return False, f"Player {player_id} does not have card {card}"
        
        # Check if card can be played in order
        last_played_card = self.played_pile[-1] if self.played_pile else 0
        if card < last_played_card:
            # Card is out of order - lose a life and discard cards
            self._handle_out_of_order(card)
            return False, f"Card {card} played out of order! Lost a life."
        
        # Card can be played
        self.player_hands[player_id].remove(card)
        self.played_pile.append(card)
        
        # Check if any cards were skipped (other players had lower cards)
        were_cards_skipped = self._handle_skipped_cards(last_played_card, card)
        
        # Check if game is lost due to skipped cards
        if self.state == GameState.GAME_LOST:
            return True, f"Card {card} played but cards were skipped! Lost a life. Game over!"
        
        # Check if level is complete
        if self._is_level_complete():
            self._complete_level()
            if were_cards_skipped:
                return True, f"Card {card} played successfully! Level {self.current_level - 1} complete! But cards were skipped - lost a life."
            return True, f"Card {card} played successfully! Level {self.current_level - 1} complete!"
        
        if were_cards_skipped:
            return True, f"Card {card} played but cards were skipped! Lost a life."
        
        return True, f"Card {card} played successfully!"
    
    def _handle_out_of_order(self, failed_card: int) -> None:
        """
        Handle a card being played out of order.
        
        Args:
            failed_card: The card that was played incorrectly
        """
        self.lives -= 1
        
        # Discard all cards from all players that should have been played
        last_played = self.played_pile[-1] if self.played_pile else 0
        
        for player_id in self.player_hands:
            cards_to_discard = [
                card for card in self.player_hands[player_id]
                if last_played < card < failed_card
            ]
            for card in cards_to_discard:
                self.player_hands[player_id].remove(card)
                self.discarded_cards.append(card)
        
        if self.lives <= 0:
            self.state = GameState.GAME_LOST
    
    def _handle_skipped_cards(self, last_played_card: int, played_card: int) -> bool:
        """
        Check if any players have cards that should have been played
        before the played card. Discard those cards and lose a life.
        
        Args:
            last_played_card: The card that was on top of the pile before the play
            played_card: The card that was just played
            
        Returns:
            True if cards were skipped (life lost), False otherwise
        """
        skipped_cards: List[int] = []
        
        for player_id in self.player_hands:
            cards_to_discard = [
                card for card in self.player_hands[player_id]
                if last_played_card < card < played_card
            ]
            self.player_hands[player_id] = [
                c for c in self.player_hands[player_id] if c not in cards_to_discard
            ]
            self.discarded_cards.extend(cards_to_discard)
            skipped_cards.extend(cards_to_discard)
        
        if skipped_cards:
            self.lives -= 1
            if self.lives <= 0:
                self.state = GameState.GAME_LOST
            return True
        return False
    
    def use_throwing_star(self) -> Tuple[bool, Dict[int, int]]:
        """
        Use a throwing star to discard the lowest card from each player.
        
        Returns:
            Tuple of (success, dict of player_id -> discarded_card)
        """
        if self.state != GameState.IN_PROGRESS:
            return False, {}
        
        if self.throwing_stars <= 0:
            return False, {}
        
        self.throwing_stars -= 1
        discarded = {}
        
        # Each player discards their lowest card
        for player_id in self.player_hands:
            if self.player_hands[player_id]:
                lowest_card = min(self.player_hands[player_id])
                self.player_hands[player_id].remove(lowest_card)
                self.discarded_cards.append(lowest_card)
                discarded[player_id] = lowest_card
        
        return True, discarded
    
    def _is_level_complete(self) -> bool:
        """Check if all cards have been played for the current level."""
        total_cards_in_hands = sum(len(hand) for hand in self.player_hands.values())
        return total_cards_in_hands == 0
    
    def _complete_level(self) -> None:
        """Mark the current level as complete and advance to next level."""
        self.state = GameState.LEVEL_COMPLETE
        
        # Check if game is won (all levels completed)
        if self.current_level >= self.MAX_LEVELS:
            self.state = GameState.GAME_WON
        else:
            self.current_level += 1
    
    def get_game_info(self) -> GameInfo:
        """
        Get current game information.
        
        Returns:
            Dictionary with game state information
        """
        return {
            "num_players": self.num_players,
            "current_level": self.current_level,
            "lives": self.lives,
            "max_lives": self.max_lives,
            "throwing_stars": self.throwing_stars,
            "max_throwing_stars": self.max_throwing_stars,
            "state": self.state.value,
            "played_pile": self.played_pile.copy(),
            "cards_in_play": sum(len(hand) for hand in self.player_hands.values()),
        }
    
    def get_player_hand(self, player_id: int) -> List[int]:
        """
        Get a player's hand (sorted).
        
        Args:
            player_id: ID of the player
            
        Returns:
            List of cards in player's hand
        """
        if player_id in self.player_hands:
            return sorted(self.player_hands[player_id])
        return []


def main():
    """Example game execution."""
    print("=== The Mind - Cooperative Card Game ===\n")
    
    # Create a 2-player game
    game = TheMind(num_players=2)
    
    print(f"Starting game with {game.num_players} players")
    print(f"Lives: {game.lives}, Throwing Stars: {game.throwing_stars}\n")
    
    # Play through level 1
    game.setup_level()
    print(f"Level {game.current_level} started!")
    print(f"Player 0 hand: {game.get_player_hand(0)}")
    print(f"Player 1 hand: {game.get_player_hand(1)}")
    print()
    
    # Example gameplay
    print("Game Info:")
    info = game.get_game_info()
    for key, value in info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
