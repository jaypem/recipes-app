# 🍲 RasPi Rezept-App (FastAPI + SQLite + LLM)

# 🍲 RasPi Recipe App

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
	pip install -r requirements.txt
	cp .env.example .env  # Add your LLM_API_KEY
	```
2. **Start**
	```sh
	uvicorn app.main:app --host 0.0.0.0 --port 8000
	```
3. **Systemd (optional)**
	See `systemd-recipe-app.service` for autostart on boot.

## Deployment
- Precompile Tailwind CSS for Pi (see `app/static/styles.css`).
- Restrict CORS to LAN.
- DB-Backup: Copy `recipes.db` regularly.

## .env
See `.env.example` for required variables.

## License
MIT
