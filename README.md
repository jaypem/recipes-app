# 🍲 RasPi Rezept-App (FastAPI + SQLite + LLM)

LLM-gestützte Rezeptsuche (Zufall **oder** mit beliebig vielen vorgegebenen Zutaten), einstellbarer Aufwand (3 Stufen) und Zutatenmenge (3 Stufen). Rezepte lassen sich speichern und per Volltext (FTS5) durchsuchen.

## 1) Setup (Raspberry Pi 3, Python 3.10+)
```bash
# uv installieren (falls nicht vorhanden)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Projekt holen
cd ~
cp -r /mnt/data/recipe-app ./recipe-app
cd recipe-app

# Abhängigkeiten
uv sync --frozen
cp .env .env
# .env bearbeiten: LLM_API_KEY, optional LLM_API_BASE, LLM_MODEL
```

## 2) Starten (Entwicklung)
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Im Heimnetz öffnen: http://<IP-des-Pi>:8000
```

## 3) Produktion (systemd)
Ersetze `User=pi`/Pfad falls abweichend.
```ini
# /etc/systemd/system/recipeapp.service
[Unit]
Description=RasPi Recipe App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/recipe-app
Environment=PYTHONPATH=/home/pi/recipe-app
ExecStart=/home/pi/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload
sudo systemctl enable recipeapp
sudo systemctl start recipeapp
```

## 4) Nutzung
- **🎲 Zufall** oder **🧺 Zutaten** wählen
- Aufwand ⚙️ (1–3) und Zutatenmenge 🧾 (1–3) setzen
- Bei **Zutaten-Modus**: beliebig viele Zutaten kommasepariert eintragen
- **🔍 Rezept finden** → **💾 speichern** möglich
- **🔎 Suche** unter _Gespeichert_ (FTS5, mehrere Wörter möglich)

## 5) Anpassungen / Best Practices
- LLM-Provider via `.env` steuerbar (`LLM_API_BASE`, `LLM_MODEL`), HTTPX mit Timeout
- Striktes JSON-Contract + Pydantic-Validierung
- SQLite-FTS5 + Trigger für robuste Suche
- Minimaler, emoji-freundlicher UI
- Keine globalen Mutables; DB via Context Manager
- Für Offline-Betrieb: Fallback-Prompts/Cache ergänzen

Viel Spaß! 🚀
