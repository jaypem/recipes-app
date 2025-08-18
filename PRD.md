# Project Requirements Document (PRD) – 🍲 RasPi Recipe App (FastAPI + Tailwind + SQLite)

> **Template:** The structure and level of detail in this PRD are based on the PRD.md you provided.&#x20;

---

## 1. Overview

**Goal:** A lightweight web app on **Raspberry Pi 3** that generates random recipes via **LLM API** **or** searches for recipes based on any number of specified ingredients. Results can be **saved**, **searched** (keyword search) and **recalled**.
**UI:** **Tailwind CSS** (with emojis in the interface where appropriate).
**Backend:** **FastAPI**, **SQLite (FTS5)** for full-text search, **httpx** for LLM calls.

---

## 2. Functional requirements (user stories & behavior)

| Requirement ID | Description                   | User Story                                                                                                                                      | Expected behavior / result                                                                                                                                                                                             |
| -------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FR001**      | Mode selection                      | As a user, I want to be able to choose whether I receive a **random** recipe **or** one that matches my **specified ingredients**. | Home page shows toggle switch: 🎲 *Random* / 🧺 *Ingredients*. When *Ingredients* is selected, an input field (token input/tags) appears for **any number** of ingredients. |
| **FR002**      | Effort (3 levels)             | As a user, I want to be able to specify the **cooking effort** in 3 levels.                                                                            | Dropdown "⚙️ Effort": `1=easy`, `2=medium`, `3=difficult`. Value is transferred to LLM and displayed in the result.                                                                                                                |
| **FR003**      | Ingredient quantity (3 levels)        | As a user, I want to set the **ingredient quantity** in 3 levels.                                                                          | Dropdown "🧾 Ingredient quantity: `1=small`, `2=medium`, `3=large`. LLM adjusts the number of ingredients accordingly. |
| **FR004**      | LLM recipe generation          | As a user, I want to receive a suitable recipe at the touch of a button.                                                                         | The **🔍 Findrecipe** button calls the backend endpoint, which addresses the LLM with a structured prompt; returns **strict JSON** with fields (title, servings, time, difficulty, ingredient quantity, tags, ingredients\[], steps\[]). |
| **FR005**      | Recipe display            | As a user, I want to see the recipe clearly. | Recipe page shows: Title 🍽️, Servings 👥, Time ⏱️, Difficulty ⚙️, Ingredient quantity 🧾, Ingredient list 🧪, Steps 🍳, tags 🏷️; UI with Tailwind components and emojis. |
| **FR006**      | Save                      | As a user, I want to **save** a recipe. | Button **💾Speichern** persistiert das Rezept in SQLite; serverseitig werden auch *ingredients\_text* und *steps\_text* für FTS gepflegt.                                                                                         |
| **FR007**      | List of saved recipes    | As a user, I want to see my saved recipes.                                                                                    | The **Saved** page lists entries (title, time, effort, ingredient quantities). Clicking on an entry opens the detailed view.                                                                                                                    |
| **FR008**      | Full-text search (keywords)    | As a user, I want to search the saved recipes using **keywords**.                                                            | The search field (🔎) filters by title, ingredients, and steps using **FTS5**. Results appear as a list sorted by relevance (BM25). |
| **FR009**      | Display search results            | As a user, I want to be able to display results again. | Clicking on a search result opens the recipe details page. |
| **FR010**      | Löschen                        | Als Nutzer\:in möchte ich gespeicherte Rezepte löschen.                                                                                         | Button **🗑️ Delete** removes the entry including FTS index maintenance (trigger). Security prompt before deletion. |
| **FR011**      | Error handling LLM           | As a user, I want to receive traceable errors.                                                                                     | In case of timeout/rate limit/invalid JSON: friendly message (with retry note) and logging on the server side; form values are retained.                                                                                             |
| **FR012**      | Local access                | As a user, I want to be able to reliably access the app on my home network.                                                                             | Service runs on `0.0.0.0:8000`. Systemd service ensures autostart & restart. |
| **FR013**      | Internationalization (easy) | As a user, I want a German interface. | UI texts in German; spätere Erweiterbarkeit (i18n) vorgesehen (Out-of-Scope für MVP).                                                                                                                                                |
| **FR014**      | Security basics          | As an operator, I want to manage keys securely.                                                                                             | `.env` with `LLM_API_KEY` (not in the repo). No storage of secrets in plain text in the code.                                                                                                                                       |
| **FR015**      | Accessible UI                | As a user, I want an easy-to-read UI.                                                                                                  | Contrasts, focus styles, semantic HTML structure; Tailwind utility classes according to WCAG basics.                                                                                                                                    |

---

## 3. Non-functional requirements (NFR)

* **Performance (Pi 3):** Initial response < **4–6 s** (depending on LLM), UI first paint < **1 s** on LAN.
* **Resources:** RAM footprint < **200 MB** at runtime; no node build chain on the Pi in continuous operation.
* **Availability:** Systemd service `Restart=always`.
* **Security:** No external write interface except app functions; CORS restrictive by default (LAN).
* **Maintainability:** Clean module separation (API/DB/LLM/UI), types via Pydantic, 1-click backup of the SQLite DB.
* **Portability:** Python **3.10+**, package management via **uv**.

---

## 4. Architecture & Technology

* **Frontend:** Server-rendered **Jinja2** + **Tailwind CSS**.

* **Tailwind Build:** *Recommendation:* **Pre-compile** CSS (e.g., on dev machine) and **deploy statically** (Pi only renders HTML). Alternatively, **Play CDN** for MVP, build later.
* **Backend:** **FastAPI**, REST-like endpoints.
* **LLM connection:** **OpenAI-compatible** `/chat/completions` via **httpx** (timeout, error handling, JSON parsing).
* **Database:** **SQLite** + **FTS5** (title/ingredients\_text/steps\_text). Triggers keep FTS in sync.
* **Deployment:** `uv run uvicorn ...`, **systemd** for autostart.

---

## 5. Datenmodell (MVP)

**Recipe**

* `id: int`
* `slug: str` (kurz, share-fähig im LAN)
* `title: str`
* `servings: int`
* `time_minutes: int`
* `difficulty: int (1..3)`
* `ingredient_load: int (1..3)`
* `tags: list[str]`
* `ingredients: list[str]` *(auch aggregiert zu `ingredients_text` für FTS)*
* `steps: list[str]` *(auch aggregiert zu `steps_text` für FTS)*
* `created_at: datetime`
* **FTS-Tabelle:** `recipes_fts(title, ingredients_text, steps_text)` mit `content_rowid = id`.

---

## 6. API-Spezifikation (MVP)

* `GET /` – Formular (🎲/🧺, ⚙️, 🧾, Zutaten-Input) – **Tailwind + Emojis**
* `POST /generate` – Body: `{ mode, difficulty, ingredient_load, ingredients? }` → **HTML** (Rezeptansicht)
* `POST /save` – Body: Felder von Recipe → **302** auf `/recipe/{id}`
* `GET /recipe/{id}` – Detailansicht
* `GET /saved?q=` – Liste gespeicherter Rezepte (FTS-Suche)
* `POST /delete/{id}` – Löschen → **302** `/saved`
* `GET /healthz` – 200 OK

**Error codes:**

* 400 (invalid parameters), 502 (LLM error), 504 (timeout), 500 (unexpected).

---

## 7. UX flows (lean)

1. **Random recipe**
   Start → 🎲 → Set ⚙️/🧾 → **🔍** → Recipe page → **💾** optional.

2. **Ingredient-based**
   Start → 🧺 → Ingredients (any number, tags field) + ⚙️/ 🧾 → **🔍** → Recipe page → **💾** optional.

3. **Saved & Search**
   **💾 Saved** → 🔎 Keyword search → Hit list → Detail view → **🗑️** optional.

---

## 8. UI guidelines (Tailwind + emojis)

* **Layout:** Container, e.g., `max-w-3xl mx-auto p-4`.
* **Form controls:** `flex flex-col gap-3`, focus styles `focus:ring`.
* **Buttons:** Primary: `rounded-xl px-4 py-2 font-semibold` (e.g. `bg-teal-400`), hover/focus states.
* **Lists:** Results as `divide-y divide-slate-700`.
* **Emojis:** Sparingly but consistently used for navigation/labels: 🧺, 🎲, 🔍, 💾, 🗑️, 🍳, 🧪, ⏱️, ⚙️.

---
## 9. Prompt contract (best practice, compact)

* **System:** "Respond **exclusively** with **valid** JSON; fields: `title`, `servings`, `time_minutes`, `difficulty(1..3)`, `ingredient_load(1..3)`, `tags[]`, `ingredients[]`, `steps[]` (short & numberable)."
* **User:** Contains mode (RANDOM **or** INGREDIENTS incl. list), selected levels, notes "no exotic ingredients," order of magnitude of the number of ingredients per level.
* **Parsing:** Extract regex `{…}` → `json.loads` → Pydantic validation.
* **Fallback:** In case of invalid JSON, a corrective second attempt (same temperature, stricter system prompt).

**Mini snippet (Python, heavily abbreviated):**

```python
payload={"model":MODEL,"messages":[
  {"role":"system","content":"Antworte nur mit gültigem JSON (siehe Felder)…"},
  {"role":"user","content":render_prompt(mode, ingredients, diff, load)}
],"temperature":0.7}
r=client.post(f"{BASE}/chat/completions", headers=auth, json=payload, timeout=60)
data=json.loads(extract_json(r.json()["choices"][0]["message"]["content"]))
recipe=Recipe(**data)
```

---

## 10. Edge Cases

* **LLM provides too many/too few ingredients** → server-side soft validation (warning message; app still displays).
* **Empty search** → show most recent recipes; **no hits** → empty state with tip.
* **Timeout/rate limit** → user notification + retry link.
* **Special characters in ingredients** → normalize/trim.
* **Pi resources scarce** → deploy Tailwind **precompiled**.

---

## 11. Success Metrics

* **TtF (Time-to-First-Recipe):** < 6 s median.
* **Search latency:** < 150 ms (local, FTS).
* **Error rate LLM calls:** < 2% (over 24 hours).
* **Retention:** ≥ 30% usage with at least 1 saved recipe.

---

## 12. Acceptance criteria (MVP)

* Selection **🎲/🧺** + **⚙️** + **🧾** available; any number of ingredients possible.
* **Show recipe** including emojis; **💾 Save** works.
* **Full-text search** of saved recipes returns relevant results (title/ingredients/steps).
* **Detail view** available from search results.
* **Delete** with confirmation.
* UI is **Tailwind-based** (no custom CSS required).
* App runs stably on **Raspberry Pi 3** in home network, autostart can be activated.

---

## 13. Not in MVP (nice-to-have)

* Edit saved recipes (inline edit).
* Filter by tags/difficulty/ingredient quantity in the saved list.
* Export/import (JSON/CSV).
* Allergens/dietary preferences.
* Multilingualism.

---

## 14. Risks & countermeasures

* **LLM costs/rate limits:** Caching of short-term results; reasonable timeouts, backoff retry.
* **Invalid JSON:** Strict system prompt, JSON schema example, emergency repair.
* **Pi performance:** No node builds on the Pi; build Tailwind beforehand; moderate Uvicorn workers (1-2).
* **DB corruption in case of power loss:** Regular SQLite backups; `journal_mode=WAL` (optional).

---

## 15. Milestones

1. **M1 – Basic framework**: FastAPI, Tailwind integrated, form & detail page.
2. **M2 – LLM integration**: Prompt contract, generation, error paths.
3. **M3 – Persistence & Search**: SQLite + FTS5, saving, list, search, details.
4. **M4 – Production**: systemd service, README for deployment, minor hardening.
5. **M5 – Polishing**: accessibility checks, empty states, UI fine-tuning.

---

## 16. Open questions

* Should **editing**/tagging already be possible in the MVP?
* Desired **dietary restrictions** (vegan, gluten-free, etc.) and whether they should be included in the prompt?
* **Offline fallback** (e.g., local sample recipes) if LLM is not available?

---

**Ready for implementation.** If you like, I can provide you with a Tailwind-based HTML template for start, result, and save views (compatible with your Pi project) and adapt the existing code base to it.
