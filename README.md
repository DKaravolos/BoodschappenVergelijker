# BoodschappenApp

A local web app for comparing prices of vegetarian meat alternatives across four Dutch
supermarkets: **Albert Heijn, Jumbo, Vomar, and Dekamarkt**. Each store is scraped
server-side and prices are stored as append-only snapshots in SQLite, so you can track
promotions over time and find the best deal.

Domain terminology lives in [`CONTEXT.md`](CONTEXT.md); the implementation plan and DB
schema in [`tasks/plan.md`](tasks/plan.md).

## Status

Early development. Phase 1 (foundation) and the Albert Heijn scraper are done:

- SQLite schema + database module (`backend/database.py`)
- Pydantic response models + FastAPI app shell (`/health`, `/products`, `/discounts`, `/scrape`)
- Albert Heijn scraper (`backend/scrapers/ah.py`)

`/products`, `/discounts`, and `POST /scrape` are still placeholders — they return empty/stub
responses until the scrape pipeline (Task 6) is wired up. The frontend is scaffold-only.

See [`HANDOFF.md`](HANDOFF.md) for the current state and next steps.

## Stack

- **Backend:** Python 3.12, FastAPI, httpx, SQLite — managed with [`uv`](https://docs.astral.sh/uv/).
- **Frontend:** Vite + React + TypeScript (`frontend/`, scaffold).
- **Monorepo:** root `package.json` runs both dev servers via `concurrently`.

## Layout

```
backend/
  database.py        SQLite schema, get_db(), init_db(), reset_db()
  models.py          Pydantic response models
  main.py            FastAPI app + routes
  scrapers/
    base.py          ScrapedItem + ScraperError (shared scraper interface)
    ah.py            Albert Heijn scraper
  tests/             pytest suite
frontend/            Vite + React app (scaffold)
tasks/               plan.md + todo.md
CONTEXT.md           domain glossary
```

## Setup

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and Node.js, then:

```bash
uv sync                          # backend deps into .venv
npm install                      # root dev tooling (concurrently)
npm install --prefix frontend    # frontend deps
```

## Running

```bash
npm run dev
```

Starts backend on http://localhost:8000 and frontend on http://localhost:5173.

Backend only:

```bash
uv run uvicorn backend.main:app --reload --port 8000
```

Health check: http://localhost:8000/health → `{"status": "ok"}`.
API docs (Swagger): http://localhost:8000/docs.

## See a scrape result

The Albert Heijn scraper runs standalone and prints how many items it fetched plus the
first one. This hits AH's live API — no login or API key needed (it uses an anonymous
token):

```bash
uv run python -m backend.scrapers.ah
```

Example output:

```
Scraped 92 AH items
First item: ScrapedItem(supermarket='ah', store_name='AH Terra Plantaardige burger 3-pack', brand='AH Terra', pack_size='3 stuks', regular_price=8.97, sale_price=None, loyalty_price=8.52)
```

> **Note:** this runs the scraper in isolation and prints to the console; it does **not**
> write to the database yet. Storing snapshots via `POST /scrape` arrives with Task 6.

## Testing

```bash
uv run pytest
```

## Data

The SQLite database is created automatically at `backend/data/boodschappen.db` on first
startup and is gitignored. To wipe and recreate the schema, call `reset_db()` from
`backend/database.py`.
