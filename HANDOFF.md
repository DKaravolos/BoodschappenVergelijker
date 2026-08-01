# HANDOFF — BoodschappenApp
Last updated: 2026-08-01

## ▶️ START HERE (fresh session)
Phase 1 (Foundation) and the first scraper (Albert Heijn) are complete and merged to `main`. Backend has a SQLite schema module, Pydantic response models, placeholder FastAPI routes, and a working AH scraper (live run: 92 items). 5 tests green. **Next action: Task 5 — product matching logic** (`backend/matching.py`), which has one real design decision to settle first (see NEXT SESSION #1). No blockers. Note: everything is pushed **except** the doc-state commit `5dace09` (NOT PUSHED).

---

## Session Blocks

► Phase 1 + AH scraper (session 2026-08-01, PUSHED 7a17680 / doc commit 5dace09 NOT PUSHED)
- Task 2 — `backend/database.py`: schema init, `get_db()`, `reset_db()`. FK enforcement via per-connection `PRAGMA foreign_keys = ON` (deliberate; SQLite ignores FKs otherwise). 5 tests in `backend/tests/test_database.py`. Commits `35b4e51`, `5f2e1b0`.
- Task 3 — `backend/models.py` (Product/Listing/PriceSnapshot/ScrapeRun) + placeholder routes `/products`, `/discounts`, `/scrape`. Commit `efa67d4`.
- Task 4 — `backend/scrapers/{base,ah}.py`: `ScrapedItem` dataclass + `ScraperError`, AH scraper. Live run 92 items. Commit `5b3cd59`.
- Tasks 3 + 4 built in parallel via subagents in git worktrees, then merged. Both passed a two-axis `/code-review`.
- Checked in project skills + commands; gitignored `.claude/worktrees/`. Commit `7ba5666`.
- Task-state docs updated (`tasks/todo.md`, `tasks/plan.md`). Commit `5dace09` (NOT PUSHED).

---

## Outstanding actions owner/others

- [ ] `rapidfuzz` not declared in `pyproject.toml` — add before Task 5 (fuzzy matching needs it). — @owner (manages pyproject/deps)
- [ ] `backend/requirements.txt` vs `pyproject.toml` drift (`rapidfuzz`, `playwright` only in requirements.txt) — pick one source of truth. — @owner
- [ ] Push `5dace09` and open/confirm `task2` → `main` on GitHub if not already. — @owner

---

## NEXT SESSION — pick up here

1. **Settle the name-normalization rule for Task 5** (design decision, grill first): `ScrapedItem` has `store_name`, not a normalized product `name`. Matching must derive a canonical `name` from `store_name`/`brand`/`pack_size`. Decide the rule with the owner before coding.
2. **Task 5 — `backend/matching.py`**: `resolve_product(db, item) -> int`. Identical brand+name+pack_size → same Product (backed by `products` UNIQUE constraint); >85% name similarity + same brand → same Product (rapidfuzz); else new Product. Depends on #1 and on `rapidfuzz` being installed.
3. **Task 6 — POST /scrape integration**: run AH scraper → matching → write Listings + PriceSnapshots + a `scrape_runs` row. Depends on Task 5.
4. When Task 7 implements discounts, replace `/discounts` placeholder `response_model=list[Product]` with a price-bearing model (Product has no price fields — deliberate placeholder for now).

---

## Stable Reference

### What & Why
Local web app comparing prices of vegetarian meat alternatives across 4 Dutch supermarkets (Albert Heijn, Jumbo, Vomar, Dekamarkt). FastAPI backend scrapes each store and stores append-only price snapshots in SQLite; React/Vite frontend gives search, brand filter, comparison table, discounts + favourites tabs. Full domain glossary in `CONTEXT.md`; plan + schema in `tasks/plan.md`.

### Stack & Locations
- Backend: Python 3.12, FastAPI, httpx, SQLite (`uv` managed). Code in `backend/`.
- Frontend: Vite + React + TS in `frontend/` (scaffold only; Phase 4).
- Monorepo root `package.json` runs both via `concurrently`.
- DB file: `backend/data/boodschappen.db` (gitignored; auto-created by `init_db()`).

### How to run
```bash
npm run dev            # both frontend (5173) + backend (8000)
uv run uvicorn backend.main:app --reload --port 8000   # backend only
uv run pytest          # test suite (currently 5)
uv run python -m backend.scrapers.ah                   # AH scraper standalone
```

### Key files
- `backend/database.py` — schema, `get_db()` (sets FK pragma), `init_db()`, `reset_db()`.
- `backend/models.py` — Pydantic response models; `Supermarket` is a 4-value `Literal` (deliberate, matches CONTEXT.md).
- `backend/main.py` — FastAPI app, lifespan calls `init_db()`, placeholder routes.
- `backend/scrapers/base.py` — `ScrapedItem` (frozen dataclass, the scraper interface) + `ScraperError`. No base class by design.
- `backend/scrapers/ah.py` — AH scraper; anonymous token, no login needed.

### Backlog
- Tasks 8–10: Jumbo/Vomar/Dekamarkt scrapers (each `async def scrape() -> list[ScrapedItem]`; no ABC).
- Task 11–15: frontend (compare, discounts, refresh/stale, favourites).
- Nice-to-have: weekly basket total page (see `tasks/plan.md`).
- No `.gitattributes` → LF/CRLF warnings on every commit; add one to silence.

### Loose notes
- **AH pricing:** AH exposes no separate all-shoppers sale, so `sale_price` is always `None`; an active Bonus below shelf maps to `loyalty_price`. Multi-buy ("2 voor X") → no unit price → `loyalty_price` None.
- **Windows/worktree gotcha:** a subagent's leftover uvicorn held a worktree `.venv` lock; `Stop-Process` lingering uvicorn/python before `git worktree remove`.
- **`uv add --dev`** wrongly duplicated pytest into `[project] dependencies`; verify after adding dev tools.
