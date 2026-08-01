# BoodschappenApp

Price comparison for vegetarian meat alternatives across 4 Dutch supermarkets (AH, Jumbo, Vomar, Dekamarkt). FastAPI + SQLite backend, Vite/React frontend. `uv`-managed Python 3.12.

## Commands

```bash
npm run dev                                    # both servers (backend :8000, frontend :5173)
uv run uvicorn backend.main:app --reload       # backend only
uv run pytest                                  # tests
uv run python -m backend.scrapers.ah           # run AH scraper live, print results
```

## Structure

```
backend/
  database.py        SQLite schema, get_db() (sets FK pragma), init_db(), reset_db()
  models.py          Pydantic response models; Supermarket = 4-value Literal
  main.py            FastAPI app, lifespan -> init_db(), routes
  scrapers/
    base.py          ScrapedItem (frozen dataclass = the scraper interface) + ScraperError
    ah.py            AH scraper (anonymous token, no login)
  tests/             pytest
frontend/            Vite + React (scaffold)
tasks/               plan.md, todo.md
CONTEXT.md           domain glossary
```

DB auto-created at `backend/data/boodschappen.db` (gitignored).

## Conventions

- Scrapers expose `async def scrape() -> list[ScrapedItem]`. No base class — shared `ScrapedItem` is the interface.
- Use `get_db()` for connections (it enables FK enforcement per-connection). Never `sqlite3.connect` directly.
- Prices as `float`, timestamps as ISO8601 `str`, mirroring the SQLite schema.

## Agent skills

### Issue tracker

Issues live as local markdown files under `.steering/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context repo — one `CONTEXT.md` + `docs/adr/` at root. See `docs/agents/domain.md`.
