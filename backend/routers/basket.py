from fastapi import APIRouter

from backend import queries
from backend.database import get_db
from backend.models import Basket

router = APIRouter(tags=["basket"])


@router.get("/basket", response_model=Basket)
async def get_basket():
    """Weekly basket totals across Favourites, per Supermarket."""
    with get_db() as conn:
        return queries.get_basket(conn)
