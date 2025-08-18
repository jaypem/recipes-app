from typing import Optional, List
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .db import init_db, save_recipe, get_recipe, search_recipes, delete_recipe
from .schemas import Recipe
from .llm_client import generate_recipe

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
    mode: str = Form(...),  # "random" | "ingredients"
    difficulty: int = Form(...),  # 1..3
    ingredient_load: int = Form(...),  # 1..3
    ingredients: Optional[str] = Form(None),  # comma separated
):
    ing_list: List[str] = []
    if mode == "ingredients" and ingredients:
        ing_list = [s.strip() for s in ingredients.split(",") if s.strip()]
    recipe: Recipe = generate_recipe(mode, ing_list, difficulty, ingredient_load)
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
    return RedirectResponse(url=f"/recipe/{rid}", status_code=303)


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
