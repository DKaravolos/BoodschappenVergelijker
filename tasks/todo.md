# Task List: BoodschappenApp

## Phase 1: Foundation

### Task 1: Monorepo scaffold
**Description:** Set up the flat monorepo structure with root `package.json` (concurrently start script), backend Python project, and frontend Vite+React scaffold stubs.

**Acceptance criteria:**
- [x] `npm run dev` starts both frontend (port 5173) and backend (port 8000) via concurrently
- [x] `uvicorn backend.main:app --reload` works standalone from root
- [x] `npm run dev:backend` and `npm run dev:frontend` work independently
- [x] `.gitignore` covers `__pycache__`, `*.pyc`, `node_modules`, `.venv`, `*.db`

**Files likely touched:**
- `package.json`
- `.gitignore`
- `backend/main.py`
- `backend/requirements.txt`
- `frontend/package.json`
- `frontend/vite.config.ts`

**Dependencies:** None
**Estimated scope:** Medium

---

### Task 2: SQLite schema + database module
**Description:** Create the SQLite database module that initializes the schema on startup. Tables: `products`, `listings`, `price_snapshots`, `scrape_runs` (see schema in plan.md).

**Acceptance criteria:**
- [x] `backend/database.py` exposes a `get_db()` function returning a connection
- [x] Schema is created on first startup via `CREATE TABLE IF NOT EXISTS`
- [x] Running the module twice does not error or duplicate schema

**Notes:** `get_db()` sets `PRAGMA foreign_keys = ON` per connection; module also exposes `reset_db()`. Covered by `backend/tests/test_database.py` (5 tests).

**Files likely touched:**
- `backend/database.py`

**Dependencies:** Task 1
**Estimated scope:** Small

---

### Task 3: Pydantic models + FastAPI app shell
**Description:** Define Pydantic response models for Product, Listing, PriceSnapshot, ScrapeRun. Wire up the FastAPI app with placeholder routes returning empty responses.

**Acceptance criteria:**
- [x] `GET /products` returns `[]` with correct schema
- [x] `GET /discounts` returns `[]` with correct schema
- [x] `POST /scrape` returns `{"status": "ok"}` placeholder
- [x] `GET /health` returns `{"status": "ok"}`

**Notes:** `/discounts` temporarily typed `list[Product]` (placeholder) — Product carries no price fields, so give it a price-bearing response model when Task 7 implements discounts.

**Files likely touched:**
- `backend/main.py`
- `backend/models.py`

**Dependencies:** Task 2
**Estimated scope:** Small

---

### ✅ Checkpoint: Foundation
- [x] `uvicorn backend.main:app --reload` runs, `/health` returns 200
- [x] SQLite file created with all 4 tables
- [x] `npm run dev` starts both processes

---

## Phase 2: First end-to-end path (AH)

### Task 4: Albert Heijn scraper
**Description:** Implement the AH scraper using httpx against the unofficial AH API. Fetches vegetarian meat alternatives (category filter), returns a list of raw scraped items with store name, brand, regular price, sale price, and loyalty (Bonuskaart) price.

**Acceptance criteria:**
- [x] `backend/scrapers/ah.py` exports an `async def scrape() -> list[ScrapedItem]` function
- [x] `ScrapedItem` includes: `supermarket`, `store_name`, `brand`, `pack_size`, `regular_price`, `sale_price | None`, `loyalty_price | None`
- [x] Running the scraper standalone returns at least 1 result
- [x] HTTP errors are caught and raised as a scraper-specific exception

**Notes:** `ScrapedItem` is a frozen `@dataclass` in `scrapers/base.py` (internal ingest DTO, not a Pydantic API model). AH exposes no separate all-shoppers sale, so `sale_price` is always `None` and an active Bonus maps to `loyalty_price`. Live run: 92 items.

**Files likely touched:**
- `backend/scrapers/__init__.py`
- `backend/scrapers/base.py`
- `backend/scrapers/ah.py`

**Dependencies:** Task 1
**Estimated scope:** Medium

---

### Task 5: Product matching logic
**Description:** Implement brand + fuzzy name matching. Given a `ScrapedItem`, resolve it to an existing `Product` in the DB (or create one). Uses `thefuzz` or `rapidfuzz` for string similarity.

**Acceptance criteria:**
- [x] `backend/matching.py` exports `resolve_product(conn, item: ScrapedItem) -> int` (returns product_id)
- [x] Items with identical brand + normalized name + pack size always resolve to the same Product
- [x] Items with >85% name similarity and same brand (+ same pack) resolve to the same Product
- [x] Items below threshold create a new Product

**Notes:** Uses `rapidfuzz.fuzz.token_sort_ratio` (threshold 85). Pack size is
part of Product identity (CONTEXT.md), so a match also requires equal normalized
pack size. Store names are cleaned into readable Product names (brand + pack
stripped). Covered by `backend/tests/test_matching.py` (6 tests).

**Files likely touched:**
- `backend/matching.py`

**Dependencies:** Task 2, Task 4
**Estimated scope:** Small

---

### Task 6: POST /scrape endpoint + AH integration
**Description:** Wire POST /scrape to run the AH scraper, run matching, and write Listings + PriceSnapshots to DB. Creates a `scrape_runs` record with status.

**Acceptance criteria:**
- [x] POST /scrape triggers the scraper(s), runs matching, and stores results
- [x] `scrape_runs` row created per supermarket with `started_at`, `completed_at`, `status`
- [x] On scraper error, `status = 'failed'` and `error_message` populated; endpoint still returns 200 with error info
- [x] Running twice does not duplicate Listings (upsert by supermarket + store_name; snapshots stay append-only)

**Notes:** `backend/scrape_service.py::run_scrape(supermarket=None)` runs the
scraper(s) concurrently, then persists sequentially on one connection. Covers
Tasks 8-10 too: `?supermarket=` targets one store; without it all four run
concurrently and one failing yields overall `partial` (all failing = `failed`).
Verified live that a blocked scraper returns 200 with a recorded failure.
Covered by `backend/tests/test_scrape_service.py` (5 tests, mocked scrapers).

**Files likely touched:**
- `backend/routers/scrape.py`
- `backend/scrape_service.py`

**Dependencies:** Task 3, Task 4, Task 5
**Estimated scope:** Medium

---

### Task 7: GET /products and GET /discounts endpoints
**Description:** Implement the two main read endpoints. `/products` supports `q` (search) and `brand` query params. `/discounts` supports `supermarket` filter. Both return latest price per Listing.

**Acceptance criteria:**
- [x] `GET /products?q=vivera` returns Products whose name contains "vivera" (case-insensitive; also matches brand)
- [x] `GET /products?brand=Vivera` filters by brand
- [x] Each Product in response includes its Listings, each with latest PriceSnapshot per supermarket
- [x] `GET /discounts?supermarket=ah` returns Listings where sale_price or loyalty_price is active (latest snapshot)
- [x] Missing Listings represented as an empty per-supermarket cell (frontend renders "Niet beschikbaar")

**Notes:** Implemented alongside the frontend so its API contract is real.
Read logic lives in `backend/queries.py` (latest snapshot per listing = max id,
append-only). Added price-bearing response models (`ProductComparison`,
`SupermarketListing`, `Discount`, `SupermarketStatus`). Also added `GET /brands`
(brand filter), `GET /favourites` + `POST/DELETE /favourites/{id}` (Task 15),
and `GET /scrape/status` (Task 14). Covered by `backend/tests/test_api.py`
(9 tests). Data population still needs Task 6 (scrape wiring); endpoints return
empty until then.

**Files likely touched:**
- `backend/queries.py`
- `backend/routers/products.py`, `discounts.py`, `favourites.py`, `scrape.py`
- `backend/models.py`
- `backend/main.py`

**Dependencies:** Task 6 (for data; contract implemented independently)
**Estimated scope:** Medium

---

### ✅ Checkpoint: AH data flows end-to-end
- [x] POST /scrape populates DB (matching + upsert; verified with mocked scrapers — live data needs network)
- [x] GET /products returns product data with prices
- [x] GET /discounts returns active promotions

---

## Phase 3: Remaining scrapers

### Task 8: Jumbo scraper
**Description:** Implement Jumbo scraper (httpx against Jumbo API). Includes Jumbo Extra's Kaart loyalty price.

**Acceptance criteria:**
- [x] `backend/scrapers/jumbo.py` implements the same `ScrapedItem` interface as AH
- [x] POST /scrape with `?supermarket=jumbo` stores Jumbo data (via scrape_service; needs network for live data)
- [x] Loyalty prices captured when present — see note

**Notes:** Uses the unofficial mobile API (`mobileapi.jumbo.com/v17/search`, no
auth). Prices come as integer cents. Jumbo's shelf promotions are all-shopper
sales, so a `promotionalPrice` maps to `sale_price` (not loyalty); the classic
search endpoint exposes no clean Extra's-card-only unit price, so `loyalty_price`
stays None — reasoning documented in the module. Covered by mocked-transport
unit tests in `backend/tests/test_scrapers.py`. Not live-validated: this
environment's egress policy blocks `mobileapi.jumbo.com` (403), same as it now
blocks `api.ah.nl`.

**Files likely touched:**
- `backend/scrapers/jumbo.py`
- `backend/routers/scrape.py`

**Dependencies:** Task 6
**Estimated scope:** Small

---

### Task 9: Vomar scraper
**Description:** Implement Vomar scraper. Attempt httpx first; fall back to Playwright if the site requires JS rendering. No loyalty pricing.

**Acceptance criteria:**
- [x] `backend/scrapers/vomar.py` returns `ScrapedItem` list with `loyalty_price = None`
- [x] POST /scrape includes Vomar data (via scrape_service; needs network for live data)

**Notes:** httpx (no Playwright needed for the JSON path). Vomar and Dekamarkt are
both Detailresult Groep webshops on a shared platform, so the fetch + mapping live
in `backend/scrapers/detailresult.py` and each store module just pins its config.
Neither chain has a loyalty programme, so `loyalty_price` is always None and folder
promotions map to `sale_price`. The Detailresult endpoint path/field names are a
best-effort reconstruction (isolated in one place, defensive multi-casing parser)
and need one live run to confirm — this environment blocks `www.vomar.nl` (403).
Mapping covered by unit tests in `backend/tests/test_scrapers.py`.

**Files likely touched:**
- `backend/scrapers/vomar.py`
- `backend/scrapers/detailresult.py`

**Dependencies:** Task 6
**Estimated scope:** Small–Medium (Medium if Playwright needed)

---

### Task 10: Dekamarkt scraper
**Description:** Implement Dekamarkt scraper. Attempt httpx first; fall back to Playwright if needed. No loyalty pricing.

**Acceptance criteria:**
- [x] `backend/scrapers/dekamarkt.py` returns `ScrapedItem` list with `loyalty_price = None`
- [x] POST /scrape without params runs all 4 supermarkets (concurrently, via scrape_service)
- [x] One scraper failing does not abort the others; overall `status = 'partial'`

**Notes:** Shares the Detailresult platform helper with Vomar (see Task 9 notes);
`dekamarkt.py` only pins its store config. Same reconstruction caveat and
network-block (`www.dekamarkt.nl` 403) apply. Each scraper raises `ScraperError`
on HTTP/transport failure, so the per-supermarket partial-failure handling can be
implemented cleanly in the scrape_service once Task 6 lands.

**Files likely touched:**
- `backend/scrapers/dekamarkt.py`
- `backend/scrapers/detailresult.py`
- `backend/scrape_service.py`

**Dependencies:** Task 8
**Estimated scope:** Small–Medium

---

### ✅ Checkpoint: All four supermarkets
- [x] POST /scrape runs all four (concurrently); each stores into the DB on success
- [x] A failing scraper returns partial status; the other supermarkets are still saved (tested)

---

## Phase 4: Frontend

### Task 11: Vite + React scaffold + API client
**Description:** Set up the React app with TypeScript, Tailwind (or plain CSS), and an API client that proxies to `localhost:8000`. Define TypeScript types mirroring backend Pydantic models.

**Acceptance criteria:**
- [x] `frontend/src/api/client.ts` has typed functions for `getProducts`, `getDiscounts`, `triggerScrape` (+ brands, favourites, scrape status)
- [x] Vite proxy forwards `/api/*` to `http://localhost:8000` (prefix stripped)
- [x] TypeScript types match backend response shapes (`frontend/src/types.ts`)

**Files likely touched:**
- `frontend/src/api/client.ts`
- `frontend/src/types.ts`
- `frontend/vite.config.ts`

**Dependencies:** Task 7
**Estimated scope:** Small

---

### Task 12: Compare page — search + brand filter + comparison table
**Description:** Main page with search bar, brand filter sidebar, and a comparison table showing Regular / Sale / Loyalty Price per supermarket. Variants from the same supermarket shown as sub-rows.

**Acceptance criteria:**
- [x] Typing in search bar filters products (debounced 300ms, hits GET /products?q=)
- [x] Selecting a brand filters to that brand
- [x] Comparison table has columns: Product, AH, Jumbo, Vomar, Dekamarkt
- [x] Each supermarket cell shows Regular Price, Sale Price (if active), Loyalty Price (if active)
- [x] Missing Listings show "Niet beschikbaar"
- [x] Multiple Listings per supermarket shown as variants (stacked in the cell)

**Notes:** `useAsync`/`useDebounce` hooks + `AsyncBoundary` handle loading/empty/
error states. `PriceCell` strikes the Regular Price when a deal is active and
labels Sale ("Aanbieding") vs Loyalty ("Bonus"). Verified in a real browser.

**Files likely touched:**
- `frontend/src/pages/Compare.tsx`
- `frontend/src/components/SearchBar.tsx`
- `frontend/src/components/BrandFilter.tsx`
- `frontend/src/components/ComparisonTable.tsx`

**Dependencies:** Task 11
**Estimated scope:** Large

---

### Task 13: Discounts tab — combined list with supermarket filter
**Description:** Separate tab/page showing all active Discounts across supermarkets, filterable by supermarket.

**Acceptance criteria:**
- [x] Discounts tab shows all Listings with active Sale or Loyalty price
- [x] Supermarket filter toggles (Alle / AH / Jumbo / Vomar / Dekamarkt)
- [x] Shows product name, brand, supermarket, Regular Price, discounted price, savings amount/percentage
- [x] Sorted by discount percentage descending by default (backend-sorted)

**Notes:** Filter chips (`MarketToggle`) stay visible even when a filter yields
no results, so the user is never trapped on an empty view.

**Files likely touched:**
- `frontend/src/pages/Discounts.tsx`
- `frontend/src/components/DiscountList.tsx`

**Dependencies:** Task 11
**Estimated scope:** Medium

---

### Task 14: Refresh button + scrape status + stale data timestamps
**Description:** Refresh button triggers POST /scrape, shows loading state, and displays last-scraped timestamp per supermarket. Stale data flagged visually.

**Acceptance criteria:**
- [x] Refresh button triggers scrape and shows spinner while running
- [x] After scrape, data refreshes without full page reload (shared `refreshToken`)
- [x] Each supermarket shows a "bijgewerkt X" last-updated timestamp (header strip)
- [x] If a supermarket's last scrape failed, the status strip shows a ⚠ warning

**Notes:** Timestamps live in a header status strip spanning all tabs rather than
per column. POST /scrape currently reports status only (data population is
Task 6); the refresh flow, timestamps, and failure indicator are fully wired.

**Files likely touched:**
- `frontend/src/components/RefreshButton.tsx`
- `frontend/src/components/ScrapeStatus.tsx`
- `frontend/src/pages/Compare.tsx`

**Dependencies:** Task 12
**Estimated scope:** Small

---

### Task 15: Favourites tab — mark Products, view comparison scoped to favourites
**Description:** Add ability to mark/unmark Products as Favourites. Favourites tab shows the same comparison table as Compare but scoped to marked Products only. Favourites stored in SQLite `favourites` table.

**Acceptance criteria:**
- [x] Star toggle on each Product in Compare page adds/removes it from `favourites` table
- [x] `GET /favourites` returns favourite Products with full Listing and latest price data
- [x] `POST /favourites/{product_id}` and `DELETE /favourites/{product_id}` endpoints work
- [x] Favourites tab renders same comparison table as Compare, scoped to favourites
- [x] Empty state shown when no Favourites marked

**Notes:** `favourites` table already existed in the schema. `ComparisonTable`
is reused by both Compare and Favourites. Add is idempotent (INSERT OR IGNORE);
POST unknown product -> 404. Toggling on either tab bumps the shared refresh
token so both views stay in sync. Verified end-to-end in a browser.

**Files likely touched:**
- `backend/routers/favourites.py`
- `backend/database.py` (add `favourites` table)
- `frontend/src/pages/Favourites.tsx`
- `frontend/src/components/ComparisonTable.tsx` (reuse with different data source)
- `frontend/src/api/client.ts`

**Dependencies:** Task 12
**Estimated scope:** Medium

---

### ✅ Checkpoint: Full app working end-to-end
_Verified in a real browser against seeded data (this environment blocks the
supermarket APIs, so a live scrape can't populate real data here)._
- [x] Can search for "vivera", see prices across all 4 supermarkets
- [x] "Niet beschikbaar" shown where a supermarket doesn't carry the product
- [x] Discounts tab shows deals, filterable by supermarket
- [x] Refresh button works, timestamps visible
- [x] Partial scrape failure shows warning without breaking UI (⚠ mislukt)
- [x] Favourites tab shows marked Products with comparison table
