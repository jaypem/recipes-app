import sqlite3
from contextlib import contextmanager
from typing import Optional
from .schemas import Recipe
import json, secrets

DB_PATH = "recipes.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            servings INTEGER NOT NULL,
            time_minutes INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            ingredient_load INTEGER NOT NULL,
            tags TEXT NOT NULL,
            data TEXT NOT NULL,
            ingredients_text TEXT NOT NULL,
            steps_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")
        c.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS recipes_fts
            USING fts5(title, ingredients_text, steps_text, content='recipes', content_rowid='id')
        """)
        c.execute("""CREATE TRIGGER IF NOT EXISTS recipes_ai AFTER INSERT ON recipes BEGIN
            INSERT INTO recipes_fts(rowid, title, ingredients_text, steps_text)
            VALUES (new.id, new.title, new.ingredients_text, new.steps_text);
        END;""")
        c.execute("""CREATE TRIGGER IF NOT EXISTS recipes_ad AFTER DELETE ON recipes BEGIN
            INSERT INTO recipes_fts(recipes_fts, rowid, title, ingredients_text, steps_text)
            VALUES('delete', old.id, old.title, old.ingredients_text, old.steps_text);
        END;""")
        c.execute("""CREATE TRIGGER IF NOT EXISTS recipes_au AFTER UPDATE ON recipes BEGIN
            INSERT INTO recipes_fts(recipes_fts, rowid, title, ingredients_text, steps_text)
            VALUES('delete', old.id, old.title, old.ingredients_text, old.steps_text);
            INSERT INTO recipes_fts(rowid, title, ingredients_text, steps_text)
            VALUES (new.id, new.title, new.ingredients_text, new.steps_text);
        END;""")


def _slug() -> str:
    return secrets.token_urlsafe(6)


def save_recipe(r: Recipe) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        tags_str = ",".join([t.strip() for t in r.tags])
        ingredients_text = "\n".join(r.ingredients)
        steps_text = "\n".join(r.steps)
        cur.execute(
            """INSERT INTO recipes
                (slug, title, servings, time_minutes, difficulty, ingredient_load, tags, data, ingredients_text, steps_text)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                _slug(),
                r.title,
                r.servings,
                r.time_minutes,
                r.difficulty,
                r.ingredient_load,
                tags_str,
                json.dumps(r.model_dump(), ensure_ascii=False),
                ingredients_text,
                steps_text,
            ),
        )
        return cur.lastrowid


def get_recipe(recipe_id: int) -> Optional[Recipe]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,)).fetchone()
        if not row:
            return None
        data = json.loads(row["data"])
        data["id"] = row["id"]
        data["slug"] = row["slug"]
        return Recipe(**data)


def search_recipes(q: str, limit: int = 25):
    q = q.strip()
    with get_conn() as conn:
        if not q:
            rows = conn.execute(
                "SELECT * FROM recipes ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT r.* FROM recipes_fts f
                       JOIN recipes r ON r.id = f.rowid
                       WHERE recipes_fts MATCH ?
                       ORDER BY bm25(recipes_fts) LIMIT ?""",
                (q, limit),
            ).fetchall()
        out = []
        for row in rows:
            data = json.loads(row["data"])
            data["id"] = row["id"]
            data["slug"] = row["slug"]
            out.append(Recipe(**data))
        return out


def delete_recipe(recipe_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
        return cur.rowcount > 0
