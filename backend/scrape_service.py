"""Run scrapers and persist results (Listings + Price Snapshots).

Orchestrates a Scrape: run the selected supermarket scraper(s) concurrently,
resolve each item to a Product (``matching``), upsert its Listing, and append a
Price Snapshot. Each supermarket gets its own ``scrape_runs`` row so a partial
failure is recorded per store without aborting the others -- a failed scraper
leaves that store's prior data (and its stale timestamp) untouched.

Storage rules:
- Listings are upserted by (supermarket, store_name), so re-scraping does not
  duplicate them.
- Price Snapshots are append-only (``docs/adr/0002``); every run adds new rows.
"""

import asyncio
import logging
from datetime import datetime, timezone

from backend import matching, queries
from backend.database import get_db
from backend.models import SUPERMARKETS, ScrapeResult, Supermarket
from backend.scrapers import ah, dekamarkt, jumbo, vomar
from backend.scrapers.base import ScrapedItem, ScraperError

logger = logging.getLogger(__name__)

# Module references (not the bound functions) so ``scrape`` is resolved at call
# time -- keeps the scrapers monkeypatchable in tests.
_SCRAPERS = {"ah": ah, "jumbo": jumbo, "vomar": vomar, "dekamarkt": dekamarkt}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _safe_scrape(
    market: Supermarket,
) -> tuple[Supermarket, list[ScrapedItem] | None, str | None]:
    """Run one scraper, capturing any failure instead of raising."""
    try:
        items = await _SCRAPERS[market].scrape()
        return market, items, None
    except ScraperError as exc:
        logger.warning("%s scrape failed: %s", market, exc)
        return market, None, str(exc)
    except Exception as exc:  # noqa: BLE001 - one bad scraper must not abort the run
        logger.exception("%s scrape raised unexpectedly", market)
        return market, None, f"unexpected error: {exc}"


def _store_items(conn, items: list[ScrapedItem], scraped_at: str) -> None:
    """Persist one supermarket's items: match Product, upsert Listing, add snapshot."""
    for item in items:
        product_id = matching.resolve_product(conn, item)
        listing_id = _upsert_listing(conn, product_id, item)
        conn.execute(
            "INSERT INTO price_snapshots "
            "(listing_id, scraped_at, regular_price, sale_price, loyalty_price) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                listing_id,
                scraped_at,
                item.regular_price,
                item.sale_price,
                item.loyalty_price,
            ),
        )


def _upsert_listing(conn, product_id: int, item: ScrapedItem) -> int:
    """Return the listing id for this item, inserting it if new.

    Keyed on (supermarket, store_name); an existing Listing is re-pointed at the
    resolved Product in case matching has since grouped it differently.
    """
    row = conn.execute(
        "SELECT id FROM listings WHERE supermarket = ? AND store_name = ?",
        (item.supermarket, item.store_name),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE listings SET product_id = ? WHERE id = ?", (product_id, row["id"])
        )
        return int(row["id"])
    cur = conn.execute(
        "INSERT INTO listings (product_id, supermarket, store_name) VALUES (?, ?, ?)",
        (product_id, item.supermarket, item.store_name),
    )
    return int(cur.lastrowid)


def _overall_status(errors: list[str | None]) -> str:
    """'completed' if all succeeded, 'failed' if all failed, else 'partial'."""
    failures = sum(1 for e in errors if e is not None)
    if failures == 0:
        return "completed"
    if failures == len(errors):
        return "failed"
    return "partial"


async def run_scrape(supermarket: Supermarket | None = None) -> ScrapeResult:
    """Scrape one supermarket (or all four) and persist the results.

    Never raises for a scraper failure: failures are recorded in ``scrape_runs``
    and reflected in the returned per-supermarket statuses.
    """
    targets: list[Supermarket] = [supermarket] if supermarket else list(SUPERMARKETS)

    started_at = _now()
    outcomes = await asyncio.gather(*(_safe_scrape(market) for market in targets))
    scraped_at = _now()

    with get_db() as conn:
        for market, items, error in outcomes:
            if error is None and items is not None:
                _store_items(conn, items, scraped_at)
                status = "completed"
            else:
                status = "failed"
            conn.execute(
                "INSERT INTO scrape_runs "
                "(started_at, completed_at, supermarket, status, error_message) "
                "VALUES (?, ?, ?, ?, ?)",
                (started_at, scraped_at, market, status, error),
            )
        conn.commit()
        statuses = queries.get_scrape_status(conn)

    overall = _overall_status([error for _, _, error in outcomes])
    return ScrapeResult(status=overall, statuses=statuses)
