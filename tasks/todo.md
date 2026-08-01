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
- [ ] `backend/matching.py` exports `resolve_product(db, item: ScrapedItem) -> int` (returns product_id)
- [ ] Items with identical brand + normalized name + pack size always resolve to the same Product
- [ ] Items with >85% name similarity and same brand resolve to the same Product
- [ ] Items below threshold create a new Product

**Files likely touched:**
- `backend/matching.py`

**Dependencies:** Task 2, Task 4
**Estimated scope:** Small

---

### Task 6: POST /scrape endpoint + AH integration
**Description:** Wire POST /scrape to run the AH scraper, run matching, and write Listings + PriceSnapshots to DB. Creates a `scrape_runs` record with status.

**Acceptance criteria:**
- [ ] POST /scrape triggers AH scraper and stores results
- [ ] `scrape_runs` row created with `started_at`, `completed_at`, `status`
- [ ] On scraper error, `status = 'failed'` and `error_message` populated; endpoint still returns 200 with error info
- [ ] Running twice does not duplicate Listings (upsert by supermarket + store_name)

**Files likely touched:**
- `backend/main.py` or `backend/routers/scrape.py`
- `backend/scrape_service.py`

**Dependencies:** Task 3, Task 4, Task 5
**Estimated scope:** Medium

---

### Task 7: GET /products and GET /discounts endpoints
**Description:** Implement the two main read endpoints. `/products` supports `q` (search) and `brand` query params. `/discounts` supports `supermarket` filter. Both return latest price per Listing.

**Acceptance criteria:**
- [ ] `GET /products?q=vivera` returns Products whose name contains "vivera" (case-insensitive)
- [ ] `GET /products?brand=Vivera` filters by brand
- [ ] Each Product in response includes its Listings, each with latest PriceSnapshot per supermarket
- [ ] `GET /discounts?supermarket=ah` returns Listings where sale_price or loyalty_price is active (latest snapshot)
- [ ] Missing Listings represented as `null` in the Product's supermarket entry

**Files likely touched:**
- `backend/routers/products.py`
- `backend/routers/discounts.py`
- `backend/main.py`

**Dependencies:** Task 6
**Estimated scope:** Medium

---

### ✅ Checkpoint: AH data flows end-to-end
- [ ] POST /scrape populates DB with AH products
- [ ] GET /products returns AH data with prices
- [ ] GET /discounts returns AH promotions

---

## Phase 3: Remaining scrapers

### Task 8: Jumbo scraper
**Description:** Implement Jumbo scraper (httpx against Jumbo API). Includes Jumbo Extra's Kaart loyalty price.

**Acceptance criteria:**
- [ ] `backend/scrapers/jumbo.py` implements the same `ScrapedItem` interface as AH
- [ ] POST /scrape with `?supermarket=jumbo` stores Jumbo data
- [ ] Loyalty prices captured when present

**Files likely touched:**
- `backend/scrapers/jumbo.py`
- `backend/routers/scrape.py`

**Dependencies:** Task 6
**Estimated scope:** Small

---

### Task 9: Vomar scraper
**Description:** Implement Vomar scraper. Attempt httpx first; fall back to Playwright if the site requires JS rendering. No loyalty pricing.

**Acceptance criteria:**
- [ ] `backend/scrapers/vomar.py` returns `ScrapedItem` list with `loyalty_price = None`
- [ ] POST /scrape includes Vomar data

**Files likely touched:**
- `backend/scrapers/vomar.py`

**Dependencies:** Task 6
**Estimated scope:** Small–Medium (Medium if Playwright needed)

---

### Task 10: Dekamarkt scraper
**Description:** Implement Dekamarkt scraper. Attempt httpx first; fall back to Playwright if needed. No loyalty pricing.

**Acceptance criteria:**
- [ ] `backend/scrapers/dekamarkt.py` returns `ScrapedItem` list with `loyalty_price = None`
- [ ] POST /scrape without params runs all 4 supermarkets
- [ ] One scraper failing does not abort the others; `scrape_runs.status = 'partial'`

**Files likely touched:**
- `backend/scrapers/dekamarkt.py`
- `backend/scrape_service.py`

**Dependencies:** Task 8
**Estimated scope:** Small–Medium

---

### ✅ Checkpoint: All four supermarkets
- [ ] POST /scrape runs all four, DB has data from each
- [ ] Killing the Vomar network returns partial status, other supermarkets still saved

---

## Phase 4: Frontend

### Task 11: Vite + React scaffold + API client
**Description:** Set up the React app with TypeScript, Tailwind (or plain CSS), and an API client that proxies to `localhost:8000`. Define TypeScript types mirroring backend Pydantic models.

**Acceptance criteria:**
- [ ] `frontend/src/api/client.ts` has typed functions for `getProducts`, `getDiscounts`, `triggerScrape`
- [ ] Vite proxy forwards `/api/*` to `http://localhost:8000`
- [ ] TypeScript types match backend response shapes

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
- [ ] Typing in search bar filters products (debounced, hits GET /products?q=)
- [ ] Selecting a brand filters to that brand
- [ ] Comparison table has columns: Product, AH, Jumbo, Vomar, Dekamarkt
- [ ] Each supermarket cell shows Regular Price, Sale Price (if active), Loyalty Price (if active)
- [ ] Missing Listings show "Not available"
- [ ] Multiple Listings per supermarket shown as variants (sub-rows or grouped)

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
- [ ] Discounts tab shows all Listings with active Sale or Loyalty price
- [ ] Supermarket filter toggles (AH / Jumbo / Vomar / Dekamarkt)
- [ ] Shows product name, brand, supermarket, Regular Price, discounted price, savings amount/percentage
- [ ] Sorted by discount percentage descending by default

**Files likely touched:**
- `frontend/src/pages/Discounts.tsx`
- `frontend/src/components/DiscountList.tsx`

**Dependencies:** Task 11
**Estimated scope:** Medium

---

### Task 14: Refresh button + scrape status + stale data timestamps
**Description:** Refresh button triggers POST /scrape, shows loading state, and displays last-scraped timestamp per supermarket. Stale data flagged visually.

**Acceptance criteria:**
- [ ] Refresh button triggers scrape and shows spinner while running
- [ ] After scrape, data refreshes without full page reload
- [ ] Each supermarket column shows "Last updated: X" timestamp
- [ ] If a supermarket's last scrape failed, column header shows warning indicator

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
- [ ] Star/heart toggle on each Product in Compare page adds/removes it from `favourites` table
- [ ] `GET /favourites` returns favourite Products with full Listing and latest price data
- [ ] `POST /favourites/{product_id}` and `DELETE /favourites/{product_id}` endpoints work
- [ ] Favourites tab renders same comparison table as Compare, scoped to favourites
- [ ] Empty state shown when no Favourites marked

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
- [ ] Can search for "vivera", see prices across all 4 supermarkets
- [ ] "Not available" shown where a supermarket doesn't carry the product
- [ ] Discounts tab shows deals, filterable by supermarket
- [ ] Refresh button works, timestamps visible
- [ ] Partial scrape failure shows warning without breaking UI
- [ ] Favourites tab shows marked Products with comparison table
