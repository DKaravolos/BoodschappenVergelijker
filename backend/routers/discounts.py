from fastapi import APIRouter

from backend import queries
from backend.database import get_db
from backend.models import Discount, Supermarket

router = APIRouter(tags=["discounts"])


@router.get("/discounts", response_model=list[Discount])
async def get_discounts(supermarket: Supermarket | None = None):
    """Active Discounts (Sale or Loyalty below Regular), by savings descending."""
    with get_db() as conn:
        return queries.get_discounts(conn, supermarket=supermarket)
