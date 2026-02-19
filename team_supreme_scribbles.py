"""
Team Supreme Scribbles - A Pictionary-style drawing and guessing game.

Players take turns drawing a randomly selected noun while the other
players try to guess what it is. There is no player cap and the
minimum number of players is 1.
"""

import random
from typing import Dict, List, Optional, Tuple
from enum import Enum


# Work-safe nouns referencing pop culture and funny things in general
WORD_LIST: List[str] = [
    # Pop culture icons
    "lightsaber", "hoverboard", "flux capacitor", "infinity gauntlet",
    "magic carpet", "sorting hat", "iron throne", "batmobile",
    "kryptonite", "pokeball", "tricorder", "proton pack",
    "golden snitch", "death star", "web shooter",
    # Funny everyday objects
    "rubber duck", "whoopee cushion", "bubble wrap", "lava lamp",
    "bean bag chair", "disco ball", "fanny pack", "silly string",
    "pool noodle", "snow globe", "jack in the box", "pinwheel",
    # Animals and characters
    "unicorn", "sasquatch", "yeti", "loch ness monster",
    "baby yoda", "pikachu", "minion", "shrek",
    "velociraptor", "t-rex", "narwhal", "sloth",
    # Food and drink
    "pizza slice", "fortune cookie", "corn dog", "waffle",
    "burrito", "sushi roll", "popsicle", "pretzel",
    "birthday cake", "taco", "donut", "pancake stack",
    # Random funny nouns
    "mullet", "monocle", "cactus", "trampoline",
    "jetpack", "treehouse", "hamster wheel", "kazoo",
    "boomerang", "pirate ship", "time machine", "robot butler",
    "space helmet", "roller coaster", "bunk bed", "hammock",
    "cannon", "catapult", "confetti", "megaphone",
]


class ScribblesGameState(Enum):
    """Enum representing the state of the game."""
    WAITING = "waiting"
    DRAWING = "drawing"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"


class TeamSupremeScribbles:
    """
    Main game class for Team Supreme Scribbles.

    Manages game state, word selection, drawing rounds, and scoring.
    """

    MIN_PLAYERS = 1
    DEFAULT_ROUNDS = 3

    def __init__(self, num_players: int, num_rounds: int = DEFAULT_ROUNDS):
        """
        Initialize Team Supreme Scribbles game.

        Args:
            num_players: Number of players (minimum 1, no maximum)
            num_rounds: Number of full rotation rounds to play

        Raises:
            ValueError: If number of players is less than 1
        """
        if num_players < self.MIN_PLAYERS:
            raise ValueError(
                f"Team Supreme Scribbles requires at least {self.MIN_PLAYERS} player, "
                f"got {num_players}"
            )

        self.num_players = num_players
        self.num_rounds = num_rounds
        self.state = ScribblesGameState.WAITING
        self.current_round = 0
        self.current_drawer: int = 0
        self.current_word: Optional[str] = None
        self.scores: Dict[int, int] = {i: 0 for i in range(num_players)}
        self.used_words: List[str] = []
        self.word_list: List[str] = WORD_LIST.copy()

    def start_round(self) -> dict:
        """
        Start a new drawing round: pick the next drawer and select a word.

        Returns:
            Dictionary with round info.
        """
        if self.state == ScribblesGameState.GAME_OVER:
            return {"success": False, "message": "Game is already over"}

        if self.state == ScribblesGameState.DRAWING:
            return {"success": False, "message": "A round is already in progress"}

        # Advance round counter when we cycle back to player 0
        if self.state == ScribblesGameState.WAITING:
            self.current_drawer = 0
            self.current_round = 1
        else:
            # Move to next drawer
            self.current_drawer = (self.current_drawer + 1) % self.num_players
            if self.current_drawer == 0:
                self.current_round += 1

        # Check if all rounds completed
        if self.current_round > self.num_rounds:
            self.state = ScribblesGameState.GAME_OVER
            return {
                "success": True,
                "message": "Game over!",
                "game_over": True,
                "final_scores": dict(self.scores),
            }

        # Pick a word
        self.current_word = self._pick_word()
        self.state = ScribblesGameState.DRAWING

        return {
            "success": True,
            "round": self.current_round,
            "drawer": self.current_drawer,
            "word": self.current_word,
        }

    def guess(self, player_id: int, word: str) -> Tuple[bool, str]:
        """
        Submit a guess for the current word.

        Args:
            player_id: ID of the guessing player
            word: The guessed word

        Returns:
            Tuple of (correct, message)
        """
        if self.state != ScribblesGameState.DRAWING:
            return False, "No round in progress"

        if player_id == self.current_drawer:
            return False, "The drawer cannot guess"

        if player_id not in self.scores:
            return False, "Invalid player ID"

        if self.current_word is None:
            return False, "No word selected"

        if word.strip().lower() == self.current_word.lower():
            self.scores[player_id] += 1
            self.scores[self.current_drawer] += 1
            self.state = ScribblesGameState.ROUND_END
            return True, f"Correct! The word was '{self.current_word}'"

        return False, "Incorrect guess"

    def end_drawing(self) -> Tuple[bool, str]:
        """
        End the current drawing round without a correct guess (time up or skip).

        Returns:
            Tuple of (success, message)
        """
        if self.state != ScribblesGameState.DRAWING:
            return False, "No round in progress"

        word = self.current_word
        self.state = ScribblesGameState.ROUND_END
        return True, f"Round ended. The word was '{word}'"

    def get_game_info(self) -> dict:
        """
        Get current game information (public state).

        Returns:
            Dictionary with game state information.
        """
        return {
            "num_players": self.num_players,
            "num_rounds": self.num_rounds,
            "current_round": self.current_round,
            "state": self.state.value,
            "current_drawer": self.current_drawer,
            "scores": dict(self.scores),
        }

    def get_drawer_info(self) -> dict:
        """
        Get information for the current drawer (includes the secret word).

        Returns:
            Dictionary with drawer-specific information.
        """
        return {
            "drawer_id": self.current_drawer,
            "word": self.current_word,
        }

    def _pick_word(self) -> str:
        """Pick a random word from the list, avoiding recent repeats."""
        available = [w for w in self.word_list if w not in self.used_words]
        if not available:
            # Reset if we've used all words
            self.used_words.clear()
            available = self.word_list.copy()
        word = random.choice(available)
        self.used_words.append(word)
        return word
