# Happy Hour Games

A collection of multiplayer games you can play with friends over the web. Each game is built in Python with a shared WebSocket server and served through a single web hub.

## Available Games

### 🃏 The Mind
A cooperative card game for 2–4 players. Everyone receives cards numbered 1–100 and must play them into a shared pile in ascending order — **without communicating**. Survive all twelve levels with at least one life remaining to win.

- **Players**: 2–4
- **Status**: ✅ Playable now (game logic + web UI)

### 🏰 Azrok's Republic
A politburo investment and deception game for exactly 4 players. Each player is a labor delegate representing a sector (Teachers, Builders, Miners, or Military). Some delegates are loyal Brothers of the Republic; others are secret Agents of the Drow. Invest wisely, bluff convincingly, and survive 10 rounds.

- **Players**: 4
- **Status**: ✅ Playable now (game logic + web UI)

### 🪵 Ore, Wood & Offer Letters
A resource trading and negotiation game.

- **Status**: 🚧 Coming soon

## Installation

No installation required for the base games — just Python 3.6+.

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
python3 test_azroks_republic.py
```

## Web Application (Multiplayer)

Play games with friends over a shared WebSocket server!

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

## Project Structure

- `the_mind.py` — The Mind game logic
- `azroks_republic.py` — Azrok's Republic game logic
- `server.py` — WebSocket server for the multiplayer web app
- `static/index.html` — Web frontend (HTML/CSS/JS)
- `requirements.txt` — Python dependencies
- `test_the_mind.py` — Tests for The Mind
- `test_azroks_republic.py` — Tests for Azrok's Republic
- `test_server.py` — Tests for the WebSocket server
- `example_gameplay.py` — Interactive gameplay example for The Mind
- `render.yaml` — Render deploy configuration

## Running Tests

```bash
# The Mind tests
python3 test_the_mind.py -v

# Azrok's Republic tests
python3 test_azroks_republic.py -v

# Server tests
python3 test_server.py -v
```

## Deploying to Render.com

You can deploy Happy Hour Games to [Render](https://render.com) so anyone can play over the internet.

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
