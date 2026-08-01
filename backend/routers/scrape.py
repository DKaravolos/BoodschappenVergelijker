from fastapi import APIRouter

from backend import queries
from backend.database import get_db
from backend.models import ScrapeResult, SupermarketStatus

router = APIRouter(tags=["scrape"])


@router.get("/scrape/status", response_model=list[SupermarketStatus])
async def scrape_status():
    """Per-Supermarket freshness + last-run health, for the refresh UI."""
    with get_db() as conn:
        return queries.get_scrape_status(conn)


@router.post("/scrape", response_model=ScrapeResult)
async def scrape():
    """Trigger a Scrape and report per-Supermarket status.

    NOTE: the scraper-to-database wiring (running the four scrapers, product
    matching, writing Listings + Price Snapshots) is Task 6 and not yet in
    place. Until then this endpoint returns the current per-Supermarket status
    so the refresh flow, freshness timestamps, and failure indicators in the UI
    are fully functional against real data; it does not fabricate snapshots.
    """
    with get_db() as conn:
        statuses = queries.get_scrape_status(conn)
    return ScrapeResult(status="ok", statuses=statuses)
