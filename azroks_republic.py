"""
Azrok's Republic - A politburo investment and deception game.

Players are labor delegates on the politburo of the Republic, each
representing a sector (Teachers, Builders, Miners, or Military).
Some are Brothers of the Republic; others are secret Agents of the Drow.
"""

import math
import random
from typing import Dict, List, Optional, Tuple
from enum import Enum


SECTORS = ["Teachers", "Builders", "Miners", "Military"]


class AzrokGameState(Enum):
    """Enum representing the state of the game."""
    SETUP = "setup"
    INVESTMENT_PHASE = "investment_phase"
    RESOLUTION_PHASE = "resolution_phase"
    ROUND_END = "round_end"
    GAME_WON_REPUBLIC = "game_won_republic"
    GAME_WON_DROW = "game_won_drow"


class AzroksRepublic:
    """
    Main game class for Azrok's Republic.

    Manages game state, investments, war efforts, and win conditions.
    """

    NUM_PLAYERS = 4
    MAX_ROUNDS = 10
    MAX_WAR_FAILURES = 3
    BASE_SALARY = 2
    IMPROVEMENT_COST = 7
    TAX_COST = 1
    TAX_EFFECT = 2
    POWDER_CHARGE_COST = 12
    AZROKS_DAGGER_COST = 14
    MAX_IMPROVEMENT_LEVEL = 4

    # 10 Fruits of Labor cards with various multipliers
    FRUITS_OF_LABOR_DECK = [1.5, 1.5, 1.5, 2.0, 2.0, 2.0, 2.5, 2.5, 3.0, 3.0]

    def __init__(self, num_players: int = 4):
        """
        Initialize Azrok's Republic game.

        Args:
            num_players: Number of players (must be 4)

        Raises:
            ValueError: If number of players is not 4
        """
        if num_players != self.NUM_PLAYERS:
            raise ValueError(
                f"Azrok's Republic requires exactly {self.NUM_PLAYERS} players, got {num_players}"
            )

        self.num_players = num_players
        self.state = AzrokGameState.SETUP
        self.current_round = 0

        # Player state
        self.sectors: Dict[int, str] = {i: SECTORS[i] for i in range(num_players)}
        self.roles: Dict[int, str] = {}
        self.money: Dict[int, int] = {i: 0 for i in range(num_players)}
        self.improvement_level: Dict[int, int] = {i: 1 for i in range(num_players)}

        # General Secretary
        self.general_secretary: int = 0

        # Turn tracking
        self.turn_order: List[int] = []
        self.current_turn_index: int = 0
        self.has_used_tax: Dict[int, bool] = {i: False for i in range(num_players)}

        # People pot
        self.people_pot: int = 0

        # War tracking
        self.war_failures: int = 0

        # Fruits of Labor deck
        self.fruits_deck: List[float] = []
        self.current_fruits_card: Optional[float] = None

    def setup_game(self) -> None:
        """Set up the game: assign roles, General Secretary, and shuffle deck."""
        # Assign roles: 2 Brothers, 2 Agents
        roles = [
            "Brother of the Republic", "Brother of the Republic",
            "Agent of the Drow", "Agent of the Drow",
        ]
        random.shuffle(roles)
        self.roles = {i: roles[i] for i in range(self.num_players)}

        # Assign General Secretary randomly
        self.general_secretary = random.randint(0, self.num_players - 1)

        # Prepare Fruits of Labor deck
        self.fruits_deck = self.FRUITS_OF_LABOR_DECK.copy()
        random.shuffle(self.fruits_deck)

        self.current_round = 0

    def get_war_cost(self) -> int:
        """Get the total war cost for the current round."""
        if self.current_round <= 3:
            return 1 * self.num_players
        elif self.current_round <= 6:
            return 2 * self.num_players
        else:
            return 3 * self.num_players

    def start_round(self) -> dict:
        """
        Start a new round: pay salary and determine turn order.

        Returns:
            Dictionary with round info (salaries, dice roll, turn order).
        """
        if self.state not in (AzrokGameState.SETUP, AzrokGameState.ROUND_END):
            return {"success": False, "message": "Cannot start a new round now"}

        self.current_round += 1

        if self.current_round > self.MAX_ROUNDS:
            self.state = AzrokGameState.GAME_WON_REPUBLIC
            return {"success": True, "message": "All rounds complete! The Republic wins!"}

        # Pay salary
        salaries = {}
        for pid in range(self.num_players):
            salary = self.BASE_SALARY * self.improvement_level[pid]
            self.money[pid] += salary
            salaries[pid] = salary

        # Roll for turn order
        # General Secretary is position 1, clockwise from there
        dice_roll = random.randint(1, self.num_players)
        positions = [
            (self.general_secretary + i) % self.num_players
            for i in range(self.num_players)
        ]
        start_idx = dice_roll - 1
        self.turn_order = positions[start_idx:] + positions[:start_idx]

        self.current_turn_index = 0
        self.has_used_tax = {i: False for i in range(self.num_players)}

        self.state = AzrokGameState.INVESTMENT_PHASE

        return {
            "success": True,
            "round": self.current_round,
            "salaries": salaries,
            "dice_roll": dice_roll,
            "turn_order": self.turn_order,
            "war_cost": self.get_war_cost(),
        }

    def get_current_player(self) -> Optional[int]:
        """Get the ID of the player whose turn it is."""
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return None
        if self.current_turn_index >= len(self.turn_order):
            return None
        return self.turn_order[self.current_turn_index]

    def invest_people(self, player_id: int, amount: int) -> Tuple[bool, str]:
        """
        Invest money into the People pot.

        Args:
            player_id: ID of the investing player
            amount: Amount of money to invest

        Returns:
            Tuple of (success, message)
        """
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return False, "Not in investment phase"
        if player_id != self.get_current_player():
            return False, "Not your turn"
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > self.money[player_id]:
            return False, "Not enough money"

        self.money[player_id] -= amount
        self.people_pot += amount
        return True, f"Invested ${amount} into the People"

    def invest_improvement(self, player_id: int) -> Tuple[bool, str]:
        """
        Spend $7 to improve labor tools, increasing salary multiplier.

        Args:
            player_id: ID of the investing player

        Returns:
            Tuple of (success, message)
        """
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return False, "Not in investment phase"
        if player_id != self.get_current_player():
            return False, "Not your turn"
        if self.money[player_id] < self.IMPROVEMENT_COST:
            return False, "Not enough money"
        if self.improvement_level[player_id] >= self.MAX_IMPROVEMENT_LEVEL:
            return False, "Already at maximum improvement level"

        self.money[player_id] -= self.IMPROVEMENT_COST
        self.improvement_level[player_id] += 1
        return True, f"Improved labor tools to {self.improvement_level[player_id]}X"

    def use_tax(self, player_id: int, target_id: int) -> Tuple[bool, str]:
        """
        Spend $1 to tax another player $2 (money is discarded).

        Args:
            player_id: ID of the taxing player
            target_id: ID of the player being taxed

        Returns:
            Tuple of (success, message)
        """
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return False, "Not in investment phase"
        if player_id != self.get_current_player():
            return False, "Not your turn"
        if self.has_used_tax[player_id]:
            return False, "Already used tax this turn"
        if player_id == target_id:
            return False, "Cannot tax yourself"
        if target_id not in self.money:
            return False, "Invalid target player"
        if self.money[player_id] < self.TAX_COST:
            return False, "Not enough money to tax"

        self.money[player_id] -= self.TAX_COST
        tax_amount = min(self.TAX_EFFECT, self.money[target_id])
        self.money[target_id] -= tax_amount
        self.has_used_tax[player_id] = True
        return True, f"Taxed player {target_id} for ${tax_amount}"

    def buy_powder_charge(self, player_id: int) -> Tuple[bool, str]:
        """
        Spend $12 to buy a powder charge, giving the Drow one war victory.

        Args:
            player_id: ID of the buying player

        Returns:
            Tuple of (success, message)
        """
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return False, "Not in investment phase"
        if player_id != self.get_current_player():
            return False, "Not your turn"
        if self.money[player_id] < self.POWDER_CHARGE_COST:
            return False, "Not enough money"

        self.money[player_id] -= self.POWDER_CHARGE_COST
        self.war_failures += 1

        if self.war_failures >= self.MAX_WAR_FAILURES:
            self.state = AzrokGameState.GAME_WON_DROW
            return True, "Powder charge detonated! The Drow overcome the Republic!"

        return True, (
            f"Powder charge detonated! Drow victories: "
            f"{self.war_failures}/{self.MAX_WAR_FAILURES}"
        )

    def buy_azroks_dagger(self, player_id: int) -> Tuple[bool, str]:
        """
        Spend $14 to recover Azrok's Dagger, winning the game for the Republic.

        Args:
            player_id: ID of the buying player

        Returns:
            Tuple of (success, message)
        """
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return False, "Not in investment phase"
        if player_id != self.get_current_player():
            return False, "Not your turn"
        if self.money[player_id] < self.AZROKS_DAGGER_COST:
            return False, "Not enough money"

        self.money[player_id] -= self.AZROKS_DAGGER_COST
        self.state = AzrokGameState.GAME_WON_REPUBLIC
        return True, "Azrok's Dagger recovered! The Republic wins!"

    def end_turn(self, player_id: int) -> Tuple[bool, str]:
        """
        End the current player's turn and advance to the next player.

        Args:
            player_id: ID of the player ending their turn

        Returns:
            Tuple of (success, message)
        """
        if self.state != AzrokGameState.INVESTMENT_PHASE:
            return False, "Not in investment phase"
        if player_id != self.get_current_player():
            return False, "Not your turn"

        self.current_turn_index += 1

        if self.current_turn_index >= len(self.turn_order):
            self.state = AzrokGameState.RESOLUTION_PHASE
            return True, "All players done. Ready for resolution."

        next_player = self.turn_order[self.current_turn_index]
        return True, f"Turn ended. Player {next_player}'s turn."

    def resolve_round(self) -> dict:
        """
        Resolve the round: deduct war cost, draw Fruits of Labor card,
        multiply the pot, and distribute to players.

        Returns:
            Dictionary with resolution results.
        """
        if self.state != AzrokGameState.RESOLUTION_PHASE:
            return {"success": False, "message": "Not in resolution phase"}

        result: dict = {"success": True}

        # 1) Subtract war cost from people pot
        war_cost = self.get_war_cost()
        result["war_cost"] = war_cost

        if self.people_pot >= war_cost:
            self.people_pot -= war_cost
            result["war_funded"] = True
        else:
            self.people_pot = 0
            self.war_failures += 1
            result["war_funded"] = False
            result["war_failures"] = self.war_failures

            if self.war_failures >= self.MAX_WAR_FAILURES:
                self.state = AzrokGameState.GAME_WON_DROW
                result["game_over"] = True
                result["winner"] = "drow"
                return result

        # 2) Draw Fruits of Labor card
        if self.fruits_deck:
            self.current_fruits_card = self.fruits_deck.pop(0)
        else:
            self.current_fruits_card = 1.5  # Fallback

        result["fruits_multiplier"] = self.current_fruits_card
        result["pot_before"] = self.people_pot

        # 3) Multiply remaining pot (round up)
        self.people_pot = math.ceil(self.people_pot * self.current_fruits_card)
        result["pot_after_multiply"] = self.people_pot

        # 4) Divide among players (round down), remainder stays in pot
        share = self.people_pot // self.num_players
        remainder = self.people_pot - (share * self.num_players)

        for pid in range(self.num_players):
            self.money[pid] += share

        self.people_pot = remainder
        result["share_per_player"] = share
        result["remainder"] = remainder

        # 6) Check if game is over (last round)
        if self.current_round >= self.MAX_ROUNDS:
            self.state = AzrokGameState.GAME_WON_REPUBLIC
            result["game_over"] = True
            result["winner"] = "republic"
        else:
            self.state = AzrokGameState.ROUND_END

        return result

    def get_game_info(self) -> dict:
        """
        Get current game information (public state).

        Returns:
            Dictionary with game state information.
        """
        return {
            "num_players": self.num_players,
            "current_round": self.current_round,
            "max_rounds": self.MAX_ROUNDS,
            "state": self.state.value,
            "people_pot": self.people_pot,
            "war_failures": self.war_failures,
            "max_war_failures": self.MAX_WAR_FAILURES,
            "war_cost": self.get_war_cost() if self.current_round > 0 else 0,
            "general_secretary": self.general_secretary,
            "turn_order": self.turn_order,
            "current_player": self.get_current_player(),
            "sectors": self.sectors,
            "improvement_levels": dict(self.improvement_level),
            "player_money": dict(self.money),
        }

    def get_player_info(self, player_id: int) -> dict:
        """
        Get player-specific information including their secret role.

        Args:
            player_id: ID of the player

        Returns:
            Dictionary with player-specific information.
        """
        if player_id not in self.roles:
            return {}
        return {
            "player_id": player_id,
            "sector": self.sectors[player_id],
            "role": self.roles[player_id],
            "money": self.money[player_id],
            "improvement_level": self.improvement_level[player_id],
            "salary": self.BASE_SALARY * self.improvement_level[player_id],
        }
