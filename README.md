# Checkers Vibe

Online multiplayer checkers with real-time WebSocket gameplay. Supports Ukrainian, Brazilian, and International rules on 8×8 and 10×10 boards.

## Stack

- **Backend:** Python 3.12, FastAPI, WebSockets, Redis
- **Frontend:** Vue.js 3, TypeScript, Pinia, Vite
- **Infrastructure:** Docker, Nginx

## Features

- Real-time multiplayer via WebSocket with automatic reconnect
- Three rule sets: Ukrainian, Brazilian, International
- Multi-capture sequences with highlighted continuation moves
- Game timer: per-move and game clock modes
- Draw offer / resign
- Move history
- Board orientation per player (your pieces always at the bottom)

## Quick Start

```bash
# Production
docker compose up -d

# Open http://localhost
```

```bash
# Development (hot reload)
docker compose -f docker-compose.dev.yml up
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

## Project Structure

```
checkers-vibe/
├── backend/
│   ├── app/
│   │   ├── api/          # WebSocket + REST endpoints
│   │   ├── models/       # Board, Piece, Game, Timer
│   │   ├── rules/        # Ukrainian, Brazilian, International
│   │   ├── services/     # Game logic, serializer, Redis store
│   │   └── schemas/      # Pydantic / WS message schemas
│   └── tests/            # Unit + integration tests
├── frontend/
│   └── src/
│       ├── components/   # Board, Cell, Piece, GameTimer, ...
│       ├── composables/  # useWebSocket, useCaptureTree, useTimer
│       ├── stores/       # Pinia: game, session, lobby
│       └── views/        # LobbyView, GameView
├── e2e/                  # Playwright end-to-end tests
├── docker-compose.yml
└── docker-compose.dev.yml
```

## How to Play

1. Open the app and enter your name
2. Create a room (choose rules and timer) or join an existing one
3. Share the link — the second player joins from the lobby
4. Click a piece to select it, then click a highlighted cell to move
5. Captures are mandatory; multi-capture sequences are highlighted automatically

## Running Tests

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
pytest

# Frontend
cd frontend
npm install
npm run test

# E2E
cd e2e
npm install
npx playwright test
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `SECRET_KEY` | `change-me-in-production` | Session secret key |
| `VITE_WS_URL` | *(auto)* | WebSocket base URL (dev only) |
