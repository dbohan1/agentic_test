"""
Unit tests for Azrok's Republic game.
"""

import unittest
from azroks_republic import AzroksRepublic, AzrokGameState


class TestAzroksRepublicInit(unittest.TestCase):
    """Test cases for game initialization."""

    def test_game_initialization(self):
        """Test game initializes with correct default values."""
        game = AzroksRepublic(num_players=4)
        self.assertEqual(game.num_players, 4)
        self.assertEqual(game.current_round, 0)
        self.assertEqual(game.state, AzrokGameState.SETUP)
        self.assertEqual(game.war_failures, 0)
        self.assertEqual(game.people_pot, 0)
        for pid in range(4):
            self.assertEqual(game.money[pid], 0)
            self.assertEqual(game.improvement_level[pid], 1)

    def test_invalid_player_count(self):
        """Test that non-4 player counts raise an error."""
        with self.assertRaises(ValueError):
            AzroksRepublic(num_players=2)
        with self.assertRaises(ValueError):
            AzroksRepublic(num_players=3)
        with self.assertRaises(ValueError):
            AzroksRepublic(num_players=5)


class TestAzroksRepublicSetup(unittest.TestCase):
    """Test cases for game setup."""

    def test_setup_assigns_roles(self):
        """Test that setup assigns exactly 2 Brothers and 2 Agents."""
        game = AzroksRepublic(4)
        game.setup_game()
        roles = list(game.roles.values())
        self.assertEqual(len(roles), 4)
        self.assertEqual(roles.count("Brother of the Republic"), 2)
        self.assertEqual(roles.count("Agent of the Drow"), 2)

    def test_setup_assigns_general_secretary(self):
        """Test that a general secretary is assigned."""
        game = AzroksRepublic(4)
        game.setup_game()
        self.assertIn(game.general_secretary, range(4))

    def test_setup_prepares_fruits_deck(self):
        """Test that the Fruits of Labor deck has 10 cards."""
        game = AzroksRepublic(4)
        game.setup_game()
        self.assertEqual(len(game.fruits_deck), 10)

    def test_sectors_assigned(self):
        """Test that sectors are correctly assigned."""
        game = AzroksRepublic(4)
        self.assertEqual(game.sectors[0], "Teachers")
        self.assertEqual(game.sectors[1], "Builders")
        self.assertEqual(game.sectors[2], "Miners")
        self.assertEqual(game.sectors[3], "Military")


class TestAzroksRepublicRounds(unittest.TestCase):
    """Test cases for round mechanics."""

    def _setup_game(self):
        game = AzroksRepublic(4)
        game.setup_game()
        return game

    def test_start_round_pays_salary(self):
        """Test that starting a round pays base salary to each player."""
        game = self._setup_game()
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertEqual(game.current_round, 1)
        for pid in range(4):
            self.assertEqual(game.money[pid], 2)  # base salary $2 * 1X

    def test_start_round_salary_with_improvements(self):
        """Test salary scales with improvement level."""
        game = self._setup_game()
        game.improvement_level[0] = 3
        result = game.start_round()
        self.assertEqual(game.money[0], 6)  # $2 * 3X
        self.assertEqual(game.money[1], 2)  # $2 * 1X

    def test_start_round_sets_investment_phase(self):
        """Test that starting a round transitions to investment phase."""
        game = self._setup_game()
        game.start_round()
        self.assertEqual(game.state, AzrokGameState.INVESTMENT_PHASE)

    def test_start_round_sets_turn_order(self):
        """Test that turn order is set with all 4 players."""
        game = self._setup_game()
        game.start_round()
        self.assertEqual(len(game.turn_order), 4)
        self.assertEqual(sorted(game.turn_order), [0, 1, 2, 3])

    def test_war_cost_scaling(self):
        """Test war cost increases over rounds."""
        game = self._setup_game()
        game.current_round = 1
        self.assertEqual(game.get_war_cost(), 4)  # $1 * 4 players
        game.current_round = 3
        self.assertEqual(game.get_war_cost(), 4)
        game.current_round = 4
        self.assertEqual(game.get_war_cost(), 8)  # $2 * 4 players
        game.current_round = 6
        self.assertEqual(game.get_war_cost(), 8)
        game.current_round = 7
        self.assertEqual(game.get_war_cost(), 12)  # $3 * 4 players
        game.current_round = 10
        self.assertEqual(game.get_war_cost(), 12)

    def test_cannot_start_round_during_investment(self):
        """Test that start_round fails during investment phase."""
        game = self._setup_game()
        game.start_round()
        result = game.start_round()
        self.assertFalse(result["success"])


class TestAzroksRepublicInvestments(unittest.TestCase):
    """Test cases for investment actions."""

    def _setup_game_in_progress(self):
        """Create a game in investment phase with known state."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.general_secretary = 0
        game.start_round()
        # Set known turn order and money
        game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 0
        for pid in range(4):
            game.money[pid] = 20
        return game

    def test_invest_people(self):
        """Test investing money into the People pot."""
        game = self._setup_game_in_progress()
        success, msg = game.invest_people(0, 5)
        self.assertTrue(success)
        self.assertEqual(game.money[0], 15)
        self.assertEqual(game.people_pot, 5)

    def test_invest_people_multiple_times(self):
        """Test investing into People multiple times in one turn."""
        game = self._setup_game_in_progress()
        game.invest_people(0, 3)
        success, msg = game.invest_people(0, 2)
        self.assertTrue(success)
        self.assertEqual(game.money[0], 15)
        self.assertEqual(game.people_pot, 5)

    def test_invest_people_not_enough_money(self):
        """Test investing more than available money."""
        game = self._setup_game_in_progress()
        success, msg = game.invest_people(0, 25)
        self.assertFalse(success)

    def test_invest_people_wrong_turn(self):
        """Test investing when it's not your turn."""
        game = self._setup_game_in_progress()
        success, msg = game.invest_people(1, 5)
        self.assertFalse(success)
        self.assertIn("Not your turn", msg)

    def test_invest_improvement(self):
        """Test buying a labor improvement."""
        game = self._setup_game_in_progress()
        success, msg = game.invest_improvement(0)
        self.assertTrue(success)
        self.assertEqual(game.money[0], 13)  # 20 - 7
        self.assertEqual(game.improvement_level[0], 2)

    def test_invest_improvement_max_level(self):
        """Test that improvement is capped at 4X."""
        game = self._setup_game_in_progress()
        game.improvement_level[0] = 4
        success, msg = game.invest_improvement(0)
        self.assertFalse(success)
        self.assertIn("maximum", msg)

    def test_invest_improvement_not_enough_money(self):
        """Test improvement with insufficient funds."""
        game = self._setup_game_in_progress()
        game.money[0] = 5
        success, msg = game.invest_improvement(0)
        self.assertFalse(success)

    def test_use_tax(self):
        """Test taxing another player."""
        game = self._setup_game_in_progress()
        success, msg = game.use_tax(0, 1)
        self.assertTrue(success)
        self.assertEqual(game.money[0], 19)  # 20 - 1 tax cost
        self.assertEqual(game.money[1], 18)  # 20 - 2 tax effect

    def test_use_tax_once_per_turn(self):
        """Test that tax can only be used once per turn."""
        game = self._setup_game_in_progress()
        game.use_tax(0, 1)
        success, msg = game.use_tax(0, 2)
        self.assertFalse(success)
        self.assertIn("Already used tax", msg)

    def test_use_tax_cannot_tax_self(self):
        """Test that a player cannot tax themselves."""
        game = self._setup_game_in_progress()
        success, msg = game.use_tax(0, 0)
        self.assertFalse(success)

    def test_use_tax_target_low_money(self):
        """Test taxing a player with less than $2."""
        game = self._setup_game_in_progress()
        game.money[1] = 1
        success, msg = game.use_tax(0, 1)
        self.assertTrue(success)
        self.assertEqual(game.money[1], 0)  # Only $1 was available

    def test_buy_powder_charge(self):
        """Test buying a powder charge."""
        game = self._setup_game_in_progress()
        success, msg = game.buy_powder_charge(0)
        self.assertTrue(success)
        self.assertEqual(game.money[0], 8)  # 20 - 12
        self.assertEqual(game.war_failures, 1)

    def test_buy_powder_charge_not_enough_money(self):
        """Test powder charge with insufficient funds."""
        game = self._setup_game_in_progress()
        game.money[0] = 10
        success, msg = game.buy_powder_charge(0)
        self.assertFalse(success)

    def test_buy_azroks_dagger(self):
        """Test buying Azrok's Dagger wins the game."""
        game = self._setup_game_in_progress()
        success, msg = game.buy_azroks_dagger(0)
        self.assertTrue(success)
        self.assertEqual(game.money[0], 6)  # 20 - 14
        self.assertEqual(game.state, AzrokGameState.GAME_WON_REPUBLIC)

    def test_buy_azroks_dagger_not_enough_money(self):
        """Test dagger with insufficient funds."""
        game = self._setup_game_in_progress()
        game.money[0] = 10
        success, msg = game.buy_azroks_dagger(0)
        self.assertFalse(success)


class TestAzroksRepublicTurnFlow(unittest.TestCase):
    """Test cases for turn flow and phase transitions."""

    def _setup_game_in_progress(self):
        game = AzroksRepublic(4)
        game.setup_game()
        game.general_secretary = 0
        game.start_round()
        game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 0
        for pid in range(4):
            game.money[pid] = 20
        return game

    def test_end_turn_advances_player(self):
        """Test ending a turn advances to the next player."""
        game = self._setup_game_in_progress()
        success, msg = game.end_turn(0)
        self.assertTrue(success)
        self.assertEqual(game.get_current_player(), 1)

    def test_end_turn_wrong_player(self):
        """Test that only the current player can end their turn."""
        game = self._setup_game_in_progress()
        success, msg = game.end_turn(2)
        self.assertFalse(success)

    def test_all_turns_end_triggers_resolution(self):
        """Test that all turns ending transitions to resolution phase."""
        game = self._setup_game_in_progress()
        game.end_turn(0)
        game.end_turn(1)
        game.end_turn(2)
        success, msg = game.end_turn(3)
        self.assertTrue(success)
        self.assertEqual(game.state, AzrokGameState.RESOLUTION_PHASE)

    def test_get_current_player(self):
        """Test get_current_player returns correct player."""
        game = self._setup_game_in_progress()
        self.assertEqual(game.get_current_player(), 0)
        game.end_turn(0)
        self.assertEqual(game.get_current_player(), 1)


class TestAzroksRepublicResolution(unittest.TestCase):
    """Test cases for round resolution."""

    def _setup_game_for_resolution(self, people_pot=20):
        game = AzroksRepublic(4)
        game.setup_game()
        game.general_secretary = 0
        game.start_round()
        game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 0
        game.people_pot = people_pot
        # End all turns to reach resolution
        for pid in range(4):
            game.current_turn_index = pid
            game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 4
        game.state = AzrokGameState.RESOLUTION_PHASE
        return game

    def test_resolve_round_war_funded(self):
        """Test resolution when war fund is met."""
        game = self._setup_game_for_resolution(people_pot=20)
        # Round 1 war cost = $4 (1 * 4 players)
        game.fruits_deck = [2.0] + game.fruits_deck
        result = game.resolve_round()
        self.assertTrue(result["success"])
        self.assertTrue(result["war_funded"])
        self.assertEqual(result["war_cost"], 4)

    def test_resolve_round_war_not_funded(self):
        """Test resolution when war fund is not met."""
        game = self._setup_game_for_resolution(people_pot=2)
        result = game.resolve_round()
        self.assertTrue(result["success"])
        self.assertFalse(result["war_funded"])
        self.assertEqual(game.war_failures, 1)

    def test_resolve_round_distribution(self):
        """Test that pot is multiplied and distributed correctly."""
        game = self._setup_game_for_resolution(people_pot=10)
        # War cost for round 1 = $4. Pot after war = $6.
        # Fruits multiplier = 1.5. $6 * 1.5 = $9 (rounded up).
        # $9 / 4 players = $2 each, remainder $1.
        game.fruits_deck = [1.5] + game.fruits_deck
        initial_money = {pid: game.money[pid] for pid in range(4)}
        result = game.resolve_round()
        self.assertEqual(result["pot_before"], 6)
        self.assertEqual(result["pot_after_multiply"], 9)
        self.assertEqual(result["share_per_player"], 2)
        self.assertEqual(result["remainder"], 1)
        self.assertEqual(game.people_pot, 1)
        for pid in range(4):
            self.assertEqual(game.money[pid], initial_money[pid] + 2)

    def test_resolve_round_transitions_to_round_end(self):
        """Test that resolution transitions to round end."""
        game = self._setup_game_for_resolution(people_pot=20)
        game.resolve_round()
        self.assertEqual(game.state, AzrokGameState.ROUND_END)

    def test_resolve_cannot_be_called_twice(self):
        """Test that resolve fails if not in resolution phase."""
        game = self._setup_game_for_resolution(people_pot=20)
        game.resolve_round()
        result = game.resolve_round()
        self.assertFalse(result["success"])


class TestAzroksRepublicWinConditions(unittest.TestCase):
    """Test cases for win conditions."""

    def test_republic_wins_after_10_rounds(self):
        """Test that the Republic wins after completing 10 rounds."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.current_round = 10
        game.state = AzrokGameState.RESOLUTION_PHASE
        game.people_pot = 100
        game.fruits_deck = [2.0]
        result = game.resolve_round()
        self.assertTrue(result.get("game_over"))
        self.assertEqual(result["winner"], "republic")
        self.assertEqual(game.state, AzrokGameState.GAME_WON_REPUBLIC)

    def test_drow_win_three_war_failures(self):
        """Test that the Drow win after 3 war failures."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.war_failures = 2
        game.current_round = 3
        game.state = AzrokGameState.RESOLUTION_PHASE
        game.people_pot = 0
        result = game.resolve_round()
        self.assertTrue(result.get("game_over"))
        self.assertEqual(result["winner"], "drow")
        self.assertEqual(game.state, AzrokGameState.GAME_WON_DROW)

    def test_drow_win_via_powder_charges(self):
        """Test that 3 powder charges cause a Drow victory."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.start_round()
        game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 0
        game.money[0] = 50
        game.war_failures = 2

        success, msg = game.buy_powder_charge(0)
        self.assertTrue(success)
        self.assertEqual(game.state, AzrokGameState.GAME_WON_DROW)

    def test_republic_wins_via_dagger(self):
        """Test that buying the dagger wins for the Republic."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.start_round()
        game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 0
        game.money[0] = 20

        success, msg = game.buy_azroks_dagger(0)
        self.assertTrue(success)
        self.assertEqual(game.state, AzrokGameState.GAME_WON_REPUBLIC)

    def test_republic_wins_all_rounds_via_start_round(self):
        """Test Republic wins if start_round is called beyond max rounds."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.current_round = 10
        game.state = AzrokGameState.ROUND_END
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertEqual(game.state, AzrokGameState.GAME_WON_REPUBLIC)


class TestAzroksRepublicGameInfo(unittest.TestCase):
    """Test cases for game info methods."""

    def test_get_game_info(self):
        """Test get_game_info returns correct data."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.start_round()
        info = game.get_game_info()
        self.assertEqual(info["num_players"], 4)
        self.assertEqual(info["current_round"], 1)
        self.assertEqual(info["max_rounds"], 10)
        self.assertEqual(info["state"], "investment_phase")
        self.assertIn("people_pot", info)
        self.assertIn("war_failures", info)
        self.assertIn("sectors", info)

    def test_get_player_info(self):
        """Test get_player_info returns role and sector."""
        game = AzroksRepublic(4)
        game.setup_game()
        game.start_round()
        info = game.get_player_info(0)
        self.assertEqual(info["player_id"], 0)
        self.assertEqual(info["sector"], "Teachers")
        self.assertIn(info["role"], [
            "Brother of the Republic", "Agent of the Drow"
        ])
        self.assertEqual(info["money"], 2)

    def test_get_player_info_invalid_player(self):
        """Test get_player_info with invalid player ID."""
        game = AzroksRepublic(4)
        game.setup_game()
        info = game.get_player_info(99)
        self.assertEqual(info, {})


class TestAzroksRepublicFullGame(unittest.TestCase):
    """Integration test for a full game flow."""

    def test_full_round_cycle(self):
        """Test a complete round: start -> invest -> resolve -> next round."""
        game = AzroksRepublic(4)
        game.setup_game()

        # Round 1
        game.start_round()
        game.turn_order = [0, 1, 2, 3]
        game.current_turn_index = 0

        # Each player invests $1 into people and ends turn
        for pid in range(4):
            game.invest_people(pid, 1)
            game.end_turn(pid)

        self.assertEqual(game.state, AzrokGameState.RESOLUTION_PHASE)
        self.assertEqual(game.people_pot, 4)

        # Resolve round
        result = game.resolve_round()
        self.assertTrue(result["success"])
        self.assertEqual(game.state, AzrokGameState.ROUND_END)

        # Round 2
        result = game.start_round()
        self.assertTrue(result["success"])
        self.assertEqual(game.current_round, 2)
        self.assertEqual(game.state, AzrokGameState.INVESTMENT_PHASE)


if __name__ == "__main__":
    unittest.main()
