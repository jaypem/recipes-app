import os
import base64
import html
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Query, File, UploadFile
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .db import init_db, save_recipe, get_recipe, search_recipes, delete_recipe
from .schemas import Recipe
from .llm_client import generate_recipe, extract_text_from_image, parse_recipe_from_text


load_dotenv()

app = FastAPI(title="🍲 RasPi Rezept-App")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate", response_class=HTMLResponse)
def post_generate(
    request: Request,
    mode: str = Form(...),
    difficulty: int = Form(...),
    ingredient_load: int = Form(...),
    servings: int = Form(...),
    ingredients: Optional[str] = Form(None),
):
    ing_list: List[str] = []
    if mode == "ingredients" and ingredients:
        ing_list = [s.strip() for s in ingredients.split(",") if s.strip()]
    try:
        recipe: Recipe = generate_recipe(
            mode, ing_list, difficulty, ingredient_load, servings
        )
    except Exception as e:
        return templates.TemplateResponse(
            "index.html", {"request": request, "error": str(e)}
        )
    return templates.TemplateResponse(
        "recipe.html", {"request": request, "recipe": recipe}
    )


@app.post("/save", response_class=RedirectResponse)
def post_save(
    title: str = Form(...),
    servings: int = Form(...),
    time_minutes: int = Form(...),
    difficulty: int = Form(...),
    ingredient_load: int = Form(...),
    tags: str = Form(""),
    ingredients: str = Form(""),
    steps: str = Form(""),
):
    r = Recipe(
        title=title.strip(),
        servings=int(servings),
        time_minutes=int(time_minutes),
        difficulty=int(difficulty),
        ingredient_load=int(ingredient_load),
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        ingredients=[s.strip() for s in ingredients.split("\n") if s.strip()],
        steps=[s.strip() for s in steps.split("\n") if s.strip()],
    )
    rid = save_recipe(r)
    return RedirectResponse(url=f"/recipe/{rid}?saved=1", status_code=303)


@app.get("/recipe/{recipe_id}", response_class=HTMLResponse)
def view_recipe(request: Request, recipe_id: int):
    r = get_recipe(recipe_id)
    if not r:
        return templates.TemplateResponse(
            "notfound.html", {"request": request}, status_code=404
        )
    return templates.TemplateResponse("recipe.html", {"request": request, "recipe": r})


@app.get("/saved", response_class=HTMLResponse)
def saved(request: Request, q: str = Query("", description="FTS-Suchbegriff")):
    items = search_recipes(q=q or "", limit=50)
    return templates.TemplateResponse(
        "saved.html", {"request": request, "items": items, "q": q}
    )


@app.post("/delete/{recipe_id}")
def remove(recipe_id: int):
    delete_recipe(recipe_id)
    return RedirectResponse(url="/saved", status_code=303)


@app.get("/ocr", response_class=HTMLResponse)
def ocr_form(request: Request):
    """Einfache Upload-Seite für OCR (separate Template-Datei)."""
    return templates.TemplateResponse("ocr.html", {"request": request})


# OCR: Bild hochladen und Text extrahieren (POST)
@app.post("/ocr", response_class=HTMLResponse)
async def post_ocr(request: Request, file: UploadFile = File(...)):
    """Empfängt das Bild, ruft die LLM-OCR auf und zeigt den erkannten Text an (Template)."""
    try:
        data = await file.read()
        mime = (file.content_type or "image/jpeg")
        text = extract_text_from_image(data, mime_type=mime)
        # Bild als Data-URL für die Ergebnisanzeige durchreichen
        b64 = base64.b64encode(data).decode("ascii")
        img_url = f"data:{mime};base64,{b64}"
        return templates.TemplateResponse(
            "ocr_result.html", {"request": request, "raw_text": text, "image_url": img_url}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "ocr_result.html",
            {"request": request, "raw_text": f"Fehler: {str(e)}"},
            status_code=400,
        )


@app.get("/health")
def health():
    return {"status": "ok"}


# OCR: Freitext zu Rezept parsen (POST)
@app.post("/ocr/parse", response_class=HTMLResponse, name="ocr_parse")
async def ocr_parse(request: Request, raw_text: str = Form(...)):
    try:
        recipe: Recipe = parse_recipe_from_text(raw_text)
        return templates.TemplateResponse(
            "recipe.html", {"request": request, "recipe": recipe}
        )
    except Exception as e:
        # Falls Parsing fehlschlägt, wieder die OCR-Seite mit Fehlermeldung anzeigen
        return templates.TemplateResponse(
            "ocr_result.html",
            {
                "request": request,
                "raw_text": raw_text,
                # optionales Bild-URL zurückreichen, falls im Formular enthalten
                "image_url": (await request.form()).get("image_url"),
                "error": str(e),
            },
            status_code=400,
        )
