# Implementation Plan: BoodschappenApp

## Overview

Local web app comparing prices of vegetarian meat alternatives across Albert Heijn, Jumbo, Vomar, and Dekamarkt. A Python/FastAPI backend scrapes each supermarket and stores append-only price snapshots in SQLite. A React/Vite frontend provides search, brand filtering, a comparison table, and a discounts tab.

## Architecture Decisions

- **Monorepo layout:** `frontend/` and `backend/` at root, one `package.json` for `concurrently` start script.
- **Backend is the single source of truth.** All scrapers run server-side; frontend only reads from FastAPI.
- **Scrapers use httpx first.** Playwright is added per-supermarket only if httpx proves insufficient.
- **Product matching runs at ingest time.** When a scraper stores a Listing, the matcher resolves it to an existing Product or creates a new one.
- **Append-only price history.** Each Scrape produces new `price_snapshots` rows; nothing is overwritten.
- **Partial scrape failure is non-fatal.** Per-supermarket errors are recorded in `scrape_runs`; stale data from prior Scrapes remains visible with its timestamp.

## Database Schema

```sql
CREATE TABLE products (
    id          INTEGER PRIMARY KEY,
    brand       TEXT NOT NULL,
    name        TEXT NOT NULL,       -- normalized
    pack_size   TEXT NOT NULL,       -- e.g. "200g", "4 stuks"
    UNIQUE(brand, name, pack_size)
);

CREATE TABLE listings (
    id           INTEGER PRIMARY KEY,
    product_id   INTEGER REFERENCES products(id),
    supermarket  TEXT NOT NULL,      -- 'ah' | 'jumbo' | 'vomar' | 'dekamarkt'
    store_name   TEXT NOT NULL,
    store_url    TEXT
);

CREATE TABLE price_snapshots (
    id             INTEGER PRIMARY KEY,
    listing_id     INTEGER REFERENCES listings(id),
    scraped_at     TEXT NOT NULL,    -- ISO8601
    regular_price  REAL NOT NULL,
    sale_price     REAL,             -- NULL if not on sale
    loyalty_price  REAL              -- NULL if no deal or supermarket has no card
);

CREATE TABLE favourites (
    id          INTEGER PRIMARY KEY,
    product_id  INTEGER REFERENCES products(id) UNIQUE
);

CREATE TABLE scrape_runs (
    id            INTEGER PRIMARY KEY,
    started_at    TEXT NOT NULL,
    completed_at  TEXT,
    supermarket   TEXT,              -- NULL = all
    status        TEXT NOT NULL,     -- 'running' | 'completed' | 'partial' | 'failed'
    error_message TEXT
);
```

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AH/Jumbo unofficial API breaks | High | Pin API version, add retry logic, document endpoint |
| Vomar/Dekamarkt require Playwright | Med | Base scraper interface abstracts transport; swap per supermarket |
| Fuzzy matching produces false links | Med | Log all match decisions; easy to inspect in SQLite |
| Vomar/Dekamarkt have no veg. alternatives | Low | Gracefully return empty Listings; "not available" shown in UI |

## Open Questions

- None remaining — domain fully resolved.

---

## Phase 1: Foundation

### Task 1: Monorepo scaffold
### Task 2: SQLite schema + database module
### Task 3: Pydantic models + FastAPI app shell

### Checkpoint: Foundation
- [x] `uvicorn backend.main:app` starts without errors
- [x] SQLite file created with correct schema on startup
- [x] `npm run dev` starts both frontend and backend

---

## Phase 2: First end-to-end path (AH)

### Task 4: Albert Heijn scraper
### Task 5: Product matching logic
### Task 6: POST /scrape endpoint + AH integration
### Task 7: GET /products and GET /discounts endpoints

### Checkpoint: AH data flows end-to-end
- [ ] Triggering POST /scrape populates the database
- [ ] GET /products returns AH products with latest prices
- [ ] GET /discounts returns AH Listings where sale or loyalty price is active

---

## Phase 3: Remaining scrapers

### Task 8: Jumbo scraper
### Task 9: Vomar scraper
### Task 10: Dekamarkt scraper

### Checkpoint: All four supermarkets scraped
- [ ] POST /scrape runs all four; DB contains data from each
- [ ] Partial failure for one supermarket doesn't abort others

---

## Phase 4: Frontend

### Task 11: Vite + React scaffold + API client
### Task 12: Compare page — search + brand filter + comparison table
### Task 13: Discounts tab — combined list with supermarket filter
### Task 14: Refresh button + scrape status + stale data timestamps
### Task 15: Favourites tab — mark Products, view comparison scoped to favourites

### Checkpoint: Full app working end-to-end
- [ ] User can search for a product and see prices across all four supermarkets
- [ ] "Not available" shown for supermarkets missing a Listing
- [ ] Discounts tab shows active sales/loyalty deals, filterable
- [ ] Refresh button triggers scrape; stale data displays last-scraped timestamp
- [ ] Favourites tab shows marked Products with full comparison table

## Nice to Have (out of scope for now)
- **Weekly basket total page** — sum of best prices across all Favourites per Supermarket, to decide where to do the full weekly shop
