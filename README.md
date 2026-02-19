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

No installation required for the base game — just Python 3.6+.

For the **multiplayer web application**, install the dependencies:

```bash
# Clone the repository
git clone https://github.com/dbohan1/agentic_test.git
cd agentic_test

# Install dependencies (needed for web app)
pip install -r requirements.txt

# Run the example (no dependencies needed)
python3 example_gameplay.py

# Run tests
python3 test_the_mind.py
python3 test_server.py
```

## Web Application (Multiplayer)

Play The Mind with friends over a shared WebSocket server!

### Quick Start

```bash
pip install -r requirements.txt
python3 server.py
```

Then open **http://localhost:8765** in your browser. Each player opens the URL in their own browser tab or device on the same network.

### How to Play Online

1. **Create a room** — Enter your name, a room name, and choose the number of players, then click **Create Room**.
2. **Share the room** — Other players open the same URL, enter their name, and click **Join** on the room from the list (or use **Refresh Rooms** to see available rooms).
3. **Game starts automatically** — Once all players have joined, cards are dealt and the game begins.
4. **Play cards** — Click a card in your hand to play it. Cards must be played in ascending order across all players.
5. **Use throwing stars** — Click the ⭐ button to have every player discard their lowest card.
6. **Complete levels** — After finishing a level, any player can click **Next Level** to advance.

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
- `server.py` - WebSocket server for multiplayer web app
- `static/index.html` - Web frontend (HTML/CSS/JS)
- `requirements.txt` - Python dependencies
- `test_the_mind.py` - Unit tests for game logic
- `test_server.py` - Unit tests for WebSocket server
- `example_gameplay.py` - Interactive gameplay example
- `README.md` - This file

## Running Tests

```bash
# Game logic tests
python3 test_the_mind.py -v

# Server tests
python3 test_server.py -v
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

## Deploying to Render.com

You can deploy The Mind to [Render](https://render.com) so anyone can play over the internet.

### Option A — One-Click Deploy with Blueprint

1. Push this repository to your own GitHub account (or fork it).
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New → Blueprint** and connect the GitHub repository.
4. Render will detect the `render.yaml` file and configure the service automatically.
5. Click **Apply** to create the service. Render will install dependencies and start the server.
6. Once the deploy finishes, open the URL shown in the Render dashboard (e.g. `https://the-mind-xxxx.onrender.com`) to play.

### Option B — Manual Web Service Setup

1. Push this repository to your own GitHub account (or fork it).
2. Log in to [Render Dashboard](https://dashboard.render.com/).
3. Click **New → Web Service** and connect the GitHub repository.
4. Configure the service with these settings:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
5. Optionally set the **PYTHON_VERSION** environment variable to `3.11` (or any 3.10+).
6. Click **Deploy Web Service**.
7. Once the deploy finishes, open the URL shown in the Render dashboard to play.

> **Note:** Render automatically provides a `PORT` environment variable. The server reads it at startup, so no extra configuration is needed.

## Contributing

This is a test repository for agentic tasks. Feel free to experiment and extend the implementation!

## License

This is an educational implementation for testing purposes.
