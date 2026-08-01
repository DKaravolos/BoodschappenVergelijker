from fastapi import APIRouter, HTTPException

from backend import queries
from backend.database import get_db
from backend.models import ProductComparison

router = APIRouter(tags=["favourites"])


@router.get("/favourites", response_model=list[ProductComparison])
async def get_favourites():
    """Favourite Products with the same comparison shape as /products."""
    with get_db() as conn:
        return queries.get_favourites(conn)


@router.post("/favourites/{product_id}", status_code=204)
async def add_favourite(product_id: int):
    """Mark a Product as favourite. 404 if the Product doesn't exist."""
    with get_db() as conn:
        if not queries.add_favourite(conn, product_id):
            raise HTTPException(status_code=404, detail="Product not found")


@router.delete("/favourites/{product_id}", status_code=204)
async def remove_favourite(product_id: int):
    """Unmark a Product as favourite (idempotent)."""
    with get_db() as conn:
        queries.remove_favourite(conn, product_id)
