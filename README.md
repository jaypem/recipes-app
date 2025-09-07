# 🍲 RasPi Recipe App (FastAPI + SQLite + LLM)

A lightweight web app for Raspberry Pi 3 to generate, search, and save recipes using FastAPI, Tailwind CSS, SQLite (FTS5), and an LLM API.

## Features

- 🎲 Random recipes or 🧺 ingredient-based recipes
- ⚙️ Select effort and 🧾 number of ingredients
- 💾 Save recipes, 🔎 full-text search, 🗑️ delete
- UI: Tailwind CSS, emojis, German language
- LLM integration (OpenAI-compatible, via httpx)
- SQLite with FTS5 for fast search

## Setup

### 1. **Clone & Install (via `pyproject.toml`)**

 ```sh
 git clone <repo-url>
 cd recipe-app
 # Option A: with uv (uses pyproject + uv.lock)
 uv sync
 . .venv/bin/activate

 # Option B: with pip (reads pyproject.toml)
 python -m venv .venv
 . .venv/bin/activate
 pip install .

 # Environment config
 cp .env.example .env  # add your LLM_API_KEY
 ```

### 2. **Start locally**

 ```sh
 uvicorn app.main:app --host 0.0.0.0 --port 8000
 ```

### 3. **Docker (recommended for deployment)**

 ```sh
 docker-compose up --build
 ```

 or via Makefile:

 ```sh
 make docker-up
 ```

### 4. **Systemd (optional)**

See `systemd-recipe-app.service` for autostart on boot.

## Access from another device on your network

### 1. Find your Raspberry Pi’s local IP address

 ```sh
 hostname -I
 ```

 Example output: `192.168.1.42`

### 2. Make sure the app is running (see above)

### 3. On your other device (phone, laptop, etc.), open a browser and go to

```http
http://<raspberry-pi-ip>:8000
```

 Example: `http://192.168.1.42:8000`

### Notes

- Both devices must be on the same Wi‑Fi/network.
- If you have a firewall on your Pi, ensure port 8000 is open.
- If you use Docker Desktop on Mac/Windows, replace `<raspberry-pi-ip>` with your host’s IP.

## Deployment

- Precompile Tailwind CSS for Pi (see `app/static/styles.css`).
- Restrict CORS to the LAN.
- DB backup: copy `recipes.db` regularly.

## .env

See `.env.example` for required variables.

## License

BSD-3-Clause

## Usage
- Open the app at `http://localhost:8000` (or your Pi’s IP).
- Enter ingredients comma-separated; leave the field empty for a random recipe.
- Adjust difficulty, ingredient load, and servings, then generate.
