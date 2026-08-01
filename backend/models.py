from typing import Literal

from pydantic import BaseModel

Supermarket = Literal["ah", "jumbo", "vomar", "dekamarkt"]

SUPERMARKETS: tuple[Supermarket, ...] = ("ah", "jumbo", "vomar", "dekamarkt")


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


# --------------------------------------------------------------------------- #
# API response models (read side)
#
# These are the shapes the frontend consumes. A ``ProductComparison`` bundles a
# Product with its latest per-Listing price so the compare table can render a
# Product row with one cell per Supermarket in a single request.
# --------------------------------------------------------------------------- #


class SupermarketListing(BaseModel):
    """One Listing plus its latest Price Snapshot, for the compare table."""

    listing_id: int
    supermarket: Supermarket
    store_name: str
    store_url: str | None = None
    scraped_at: str
    regular_price: float
    sale_price: float | None = None
    loyalty_price: float | None = None


class ProductComparison(BaseModel):
    """A Product with every Supermarket Listing's current price snapshot."""

    id: int
    brand: str
    name: str
    pack_size: str
    is_favourite: bool = False
    listings: list[SupermarketListing] = []


class Discount(BaseModel):
    """A Listing whose latest snapshot has an active Sale or Loyalty price."""

    listing_id: int
    product_id: int
    brand: str
    name: str
    pack_size: str
    supermarket: Supermarket
    store_name: str
    scraped_at: str
    regular_price: float
    sale_price: float | None = None
    loyalty_price: float | None = None
    best_price: float
    savings: float
    savings_pct: float


class SupermarketStatus(BaseModel):
    """Freshness/health of the most recent Scrape for one Supermarket."""

    supermarket: Supermarket
    last_scraped_at: str | None = None
    status: str | None = None
    error_message: str | None = None


class ScrapeResult(BaseModel):
    """Outcome of a POST /scrape call, with per-Supermarket status."""

    status: str
    statuses: list[SupermarketStatus] = []


class BasketProduct(BaseModel):
    """One Favourite's best price at each Supermarket, for the weekly basket."""

    product_id: int
    brand: str
    name: str
    pack_size: str
    prices: dict[Supermarket, float | None]  # None = not stocked there
    cheapest: Supermarket | None = None  # which Supermarket is cheapest for it


class SupermarketTotal(BaseModel):
    """A Supermarket's running total across the Favourites basket."""

    supermarket: Supermarket
    total: float
    available_count: int
    complete: bool  # stocks every Favourite in the basket


class Basket(BaseModel):
    """The weekly basket: best price per Favourite per Supermarket, summed.

    ``cheapest_complete`` is the cheapest Supermarket that stocks *every*
    Favourite -- i.e. where the whole weekly shop can actually be done -- or
    None when no single Supermarket carries them all.
    """

    favourite_count: int
    products: list[BasketProduct] = []
    totals: list[SupermarketTotal] = []
    cheapest_complete: Supermarket | None = None
