from fastapi import APIRouter

from backend import queries
from backend.database import get_db
from backend.models import ProductComparison

router = APIRouter(tags=["products"])


@router.get("/products", response_model=list[ProductComparison])
async def get_products(q: str | None = None, brand: str | None = None):
    """Products with latest per-Supermarket prices.

    ``q`` searches name and brand; ``brand`` filters to one brand.
    """
    with get_db() as conn:
        return queries.get_products(conn, q=q, brand=brand)


@router.get("/brands", response_model=list[str])
async def get_brands():
    """Distinct brands, for the compare-page brand filter."""
    with get_db() as conn:
        return queries.get_brands(conn)
