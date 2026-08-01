from typing import Literal

from pydantic import BaseModel

Supermarket = Literal["ah", "jumbo", "vomar", "dekamarkt"]


class Product(BaseModel):
    id: int
    brand: str
    name: str
    pack_size: str


class Listing(BaseModel):
    id: int
    product_id: int
    supermarket: Supermarket
    store_name: str
    store_url: str | None = None


class PriceSnapshot(BaseModel):
    id: int
    listing_id: int
    scraped_at: str
    regular_price: float
    sale_price: float | None = None
    loyalty_price: float | None = None


class ScrapeRun(BaseModel):
    id: int
    started_at: str
    completed_at: str | None = None
    supermarket: Supermarket | None = None
    status: str
    error_message: str | None = None
