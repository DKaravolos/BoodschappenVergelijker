from fastapi import APIRouter

from backend import queries
from backend.database import get_db
from backend.models import ScrapeResult, Supermarket, SupermarketStatus
from backend.scrape_service import run_scrape

router = APIRouter(tags=["scrape"])


@router.get("/scrape/status", response_model=list[SupermarketStatus])
async def scrape_status():
    """Per-Supermarket freshness + last-run health, for the refresh UI."""
    with get_db() as conn:
        return queries.get_scrape_status(conn)


@router.post("/scrape", response_model=ScrapeResult)
async def scrape(supermarket: Supermarket | None = None):
    """Run the scraper(s) and persist results; report per-Supermarket status.

    Without ``supermarket`` all four run; a single scraper failing does not abort
    the others (``status`` becomes 'partial'). Scraper failures are recorded in
    ``scrape_runs`` and returned in the statuses -- the endpoint still responds
    200 so the UI can surface the failure without treating it as a request error.
    """
    return await run_scrape(supermarket)
