import os
import json
from .logger import get_logger
from typing import List, Optional
from .schemas import Recipe
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()

logger = get_logger("llm_client")

LLM_BASE = os.getenv("LLM_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "API-Key fehlt. Setze GOOGLE_API_KEY oder LLM_API_KEY oder GEMINI_API_KEY."
            )
        _client = genai.Client(api_key=GOOGLE_API_KEY)
    return _client


def _prompt(
    mode: str,
    ingredients: Optional[List[str]],
    difficulty: int,
    ingredient_load: int,
    servings: int,
) -> str:
    return f"""Du bist ein Kochassistent. Liefere ein einziges valides JSON-Objekt für ein Rezept.
Anforderungen:
- Sprache: Deutsch
- Felder: title, servings, time_minutes, difficulty (1-3), ingredient_load (1-3),
    tags [min 1], ingredients [List], steps [nummerierte knappe Schritte]
- Schwierigkeit: 1=leicht, 2=mittel, 3=aufwendig
- Zutatenmenge: 1=wenig (≈5-8), 2=mittel (≈9-14), 3=viele (15+)
- Portionen: {servings}
- {("Modus: ZUFALL. Ignoriere vorgegebene Zutaten." if mode == "random" else "Modus: ZUTATEN. Verwende zwingend diese Zutaten: " + ", ".join(ingredients or []))}
- Passe das Rezept sinnvoll an die gewählte Schwierigkeit, Zutatenmenge und Portionenzahl an.
- Übertreibe nicht mit exotischen Zutaten.
- Ausgabe NUR JSON, keine Erklärungen.

Beispielstruktur:
{{
    "title": "Pasta Aglio e Olio",
    "servings": 2,
    "time_minutes": 20,
    "difficulty": 1,
    "ingredient_load": 1,
    "tags": ["pasta","schnell"],
    "ingredients": ["200 g Spaghetti","3 Knoblauchzehen","Olivenöl","Chiliflocken","Petersilie","Salz"],
    "steps": ["Wasser salzen und Spaghetti kochen.","Knoblauch in Öl sanft braten.","Spaghetti mit Öl, Chili, Petersilie mischen."]
}}
"""


def generate_recipe(
    mode: str,
    ingredients: Optional[List[str]],
    difficulty: int,
    ingredient_load: int,
    servings: int,
) -> Recipe:
    if not GOOGLE_API_KEY:
        logger.error("LLM_API_KEY fehlt. Bitte in .env setzen.")
        raise RuntimeError("LLM_API_KEY fehlt. Bitte in .env setzen.")
    try:
        logger.info(
            f"Request: mode={mode}, ingredients={ingredients}, difficulty={difficulty}, ingredient_load={ingredient_load}"
        )
        resp = _get_client().models.generate_content(
            model=LLM_MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": "Du bist ein präziser Rezeptgenerator. Antworte ausschließlich mit JSON."
                        },
                        {
                            "text": _prompt(
                                mode, ingredients, difficulty, ingredient_load, servings
                            )
                        },
                    ],
                }
            ],
            config={
                "temperature": 0.7,
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "servings": {"type": "integer"},
                        "time_minutes": {"type": "integer"},
                        "difficulty": {"type": "integer", "minimum": 1, "maximum": 3},
                        "ingredient_load": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 3,
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        },
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "steps": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "title",
                        "servings",
                        "time_minutes",
                        "difficulty",
                        "ingredient_load",
                        "tags",
                        "ingredients",
                        "steps",
                    ],
                },
            },
        )
        content = (getattr(resp, "text", None) or "").strip()
        logger.info(f"LLM response: {content}")
        obj = json.loads(content)
        return Recipe(**obj)
    except Exception as e:
        logger.exception(f"LLM Fehler: {e}")
        raise


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """
    Liest Text aus einem Bild (z. B. Foto eines Notizzettels) aus und gibt den
    erkannten Text als einfachen String zurück.
    """
    try:
        client = _get_client()
        model = os.getenv("LLM_OCR_MODEL", "gemini-2.5-flash")
        resp = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                (
                    "Extrahiere den erkannten Text so wörtlich wie möglich. "
                    "Keine Erklärungen, nur der reine Textinhalt."
                ),
            ],
        )
        content = (getattr(resp, "text", None) or "").strip()
        logger.info(f"OCR response: {content}")
        if not content:
            logger.error(f"Leere OCR-Antwort: {resp}")
            raise RuntimeError("Keine OCR-Antwort vom Modell.")
        return content
    except Exception as e:
        logger.exception(f"OCR Fehler: {e}")
        raise


def parse_recipe_from_text(raw_text: str) -> Recipe:
    """
    Konvertiert freien OCR-Text eines (mutmaßlichen) Rezepts in unser Recipe-Schema
    mittels LLM. Falls Informationen fehlen, plausibel ergänzen. Ausgabe: reines JSON.
    """
    if not GOOGLE_API_KEY:
        logger.error("LLM_API_KEY fehlt. Bitte in .env setzen.")
        raise RuntimeError("LLM_API_KEY fehlt. Bitte in .env setzen.")
    try:
        logger.info("Parse OCR-Text zu Rezept via LLM")
        client = _get_client()
        model = os.getenv("LLM_PARSE_MODEL", LLM_MODEL)
        resp = client.models.generate_content(
            model=model,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Du erhältst den aus einem Foto extrahierten Rezepttext. "
                                "Strukturiere ihn in dieses JSON-Schema. Nutze exakt Deutsch. "
                                "Wo Werte fehlen, schätze sinnvoll. Zutaten/Schritte möglichst nah am Text.\n\n"
                            )
                        },
                        {"text": raw_text},
                    ],
                }
            ],
            config={
                "temperature": 0.4,
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "servings": {"type": "integer"},
                        "time_minutes": {"type": "integer"},
                        "difficulty": {"type": "integer", "minimum": 1, "maximum": 3},
                        "ingredient_load": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 3,
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 0,
                        },
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "steps": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "title",
                        "servings",
                        "time_minutes",
                        "difficulty",
                        "ingredient_load",
                        "tags",
                        "ingredients",
                        "steps",
                    ],
                },
            },
        )
        content = (getattr(resp, "text", None) or "").strip()
        logger.info(f"Parse response: {content}")
        if not content:
            raise RuntimeError("Leere Antwort beim Parsen des OCR-Texts")
        obj = json.loads(content)
        return Recipe(**obj)
    except Exception as e:
        logger.exception(f"Parse-Fehler: {e}")
        raise
