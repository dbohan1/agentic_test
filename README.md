# The Mind - Cooperative Card Game

A Python implementation of The Mind, a cooperative card game where players must work together to play cards in ascending order without communicating verbally or through gestures.

## Game Overview

**The Mind** is a unique cooperative game that emphasizes teamwork and non-verbal communication. Players must play their cards in ascending order (1-100) by relying on intuition and synchronization with teammates.

### Objective
Complete all twelve levels of the game without losing all your life cards.

## Game Components

- **100 Number Cards**: Cards numbered 1-100
- **12 Levels**: Progressive difficulty from level 1 to 12
- **Life Cards**: Based on player count (2 players = 2 lives, 3 players = 3 lives, 4 players = 4 lives)
- **Throwing Star Cards**: Based on player count (2-4 players = 1 throwing star)

## Game Rules

### Setup
- In level 1, each player receives 1 card
- In level 2, each player receives 2 cards
- This continues until level 12, where players receive 12 cards

### Gameplay
1. **Playing Cards**: Players must play their cards in ascending order into a central pile without communicating
2. **No Communication**: No talking, gestures, or hints about cards
3. **Losing Lives**: If a player plays a card out of order, the team loses a life and discards all cards between the last played card and the incorrectly played card
4. **Using Throwing Stars**: Players can use a throwing star to have each player discard their lowest card face up
5. **Winning**: Complete all 12 levels with at least 1 life remaining
6. **Losing**: Run out of life cards

## Installation

No installation required! Just Python 3.6+.

```bash
# Clone the repository
git clone https://github.com/dbohan1/agentic_test.git
cd agentic_test

# Run the example
python3 example_gameplay.py

# Run tests
python3 test_the_mind.py
```

## Usage

### Basic Example

```python
from the_mind import TheMind

# Create a 2-player game
game = TheMind(num_players=2)

# Setup level 1
game.setup_level()

# Get player hands
print(f"Player 0 hand: {game.get_player_hand(0)}")
print(f"Player 1 hand: {game.get_player_hand(1)}")

# Play cards
success, msg = game.play_card(0, 25)
print(msg)

# Use a throwing star
success, discarded = game.use_throwing_star()
print(f"Discarded cards: {discarded}")

# Check game status
info = game.get_game_info()
print(f"Current level: {info['current_level']}")
print(f"Lives: {info['lives']}")
```

## API Reference

### TheMind Class

#### `__init__(num_players: int)`
Initialize a new game.
- **Parameters**: `num_players` - Number of players (2-4)
- **Raises**: `ValueError` if player count is invalid

#### `setup_level()`
Set up a new level by shuffling deck and dealing cards.

#### `play_card(player_id: int, card: int) -> Tuple[bool, str]`
Attempt to play a card from a player's hand.
- **Returns**: Tuple of (success: bool, message: str)

#### `use_throwing_star() -> Tuple[bool, Dict[int, int]]`
Use a throwing star to discard the lowest card from each player.
- **Returns**: Tuple of (success: bool, dict of player_id -> discarded_card)

#### `get_player_hand(player_id: int) -> List[int]`
Get a player's hand (sorted).
- **Returns**: List of cards in player's hand

#### `get_game_info() -> Dict`
Get current game information.
- **Returns**: Dictionary with game state information

## Files

- `the_mind.py` - Main game implementation
- `test_the_mind.py` - Unit tests
- `example_gameplay.py` - Interactive gameplay example
- `README.md` - This file

## Running Tests

```bash
python3 test_the_mind.py -v
```

All tests should pass:
```
test_game_initialization ... ok
test_game_lost ... ok
test_game_won ... ok
test_get_game_info ... ok
test_invalid_player_count ... ok
test_level_completion ... ok
test_level_setup ... ok
test_play_card_in_order ... ok
test_play_card_out_of_order ... ok
test_throwing_star ... ok
```

## Example Output

```
============================================================
The Mind - Interactive Example
============================================================

🎮 Starting a 2-player game!
❤️  Lives: 2
⭐ Throwing Stars: 1

------------------------------------------------------------
📊 LEVEL 1
------------------------------------------------------------
Player 0 hand: [50]
Player 1 hand: [10]

Player 1 plays 10: Card 10 played successfully!
Player 0 plays 50: Card 50 played successfully! Level 1 complete!
```

## Contributing

This is a test repository for agentic tasks. Feel free to experiment and extend the implementation!

## License

This is an educational implementation for testing purposes.
