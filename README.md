# 🍲 RasPi Rezept-App (FastAPI + SQLite + LLM)

A lightweight web app for Raspberry Pi 3 to generate, search, and save recipes using FastAPI, Tailwind CSS, SQLite (FTS5), and an LLM API.

## Features
- 🎲 Zufallsrezepte oder 🧺 Zutatenbasierte Rezepte
- ⚙️ Aufwand & 🧾 Zutatenmenge auswählbar
- 💾 Rezepte speichern, 🔎 Volltextsuche, 🗑️ löschen
- UI: Tailwind CSS, Emojis, Deutsch
- LLM-Anbindung (OpenAI-kompatibel, httpx)
- SQLite mit FTS5 für schnelle Suche


## Setup
1. **Clone & Install**
	```sh
	git clone <repo-url>
	cd recipe-app
	pip install -r requirements.txt  # or use pyproject.toml with pip install .
	cp .env.example .env  # Add your LLM_API_KEY
	```
2. **Start locally**
	```sh
	uvicorn app.main:app --host 0.0.0.0 --port 8000
	```
3. **Docker (recommended for deployment)**
	```sh
	docker-compose up --build
	```
	or use the Makefile:
	```sh
	make docker-up
	```
4. **Systemd (optional)**
	See `systemd-recipe-app.service` for autostart on boot.

## Access from another device on your network

1. Find your Raspberry Pi’s local IP address:
	```sh
	hostname -I
	```
	Example output: `192.168.1.42`

2. Make sure the app is running (see above).

3. On your other device (phone, laptop, etc.), open a browser and go to:
	```
	http://<raspberry-pi-ip>:8000
	```
	Example: `http://192.168.1.42:8000`

**Note:**
- Both devices must be on the same Wi-Fi/network.
- If you have a firewall on your Pi, ensure port 8000 is open.
- If you use Docker Desktop on Mac/Windows, replace `<raspberry-pi-ip>` with your host’s IP.

## Deployment
- Precompile Tailwind CSS for Pi (see `app/static/styles.css`).
- Restrict CORS to LAN.
- DB-Backup: Copy `recipes.db` regularly.

## .env
See `.env.example` for required variables.

## License
MIT
