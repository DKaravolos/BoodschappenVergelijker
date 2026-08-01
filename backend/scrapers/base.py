"""Shared types for supermarket scrapers.

Every scraper (AH, Jumbo, Vomar, Dekamarkt) fetches its own catalogue and maps
the results onto the same ``ScrapedItem``. That shared shape *is* the scraper
interface -- there is deliberately no base class, since the only thing scrapers
need to agree on is the item they produce.
"""

from dataclasses import dataclass


class ScraperError(Exception):
    """Raised when a scraper cannot fetch or parse supermarket data.

    Scrapers catch transport/HTTP errors (e.g. ``httpx`` exceptions) and
    re-raise them as this type so callers have a single scraper-level error to
    handle regardless of which supermarket failed.
    """


@dataclass(frozen=True, slots=True)
class ScrapedItem:
    """A single supermarket listing with its current price snapshot.

    Field meanings follow the domain language in ``CONTEXT.md``:

    - ``regular_price``: standard shelf price, no promotion or loyalty card.
    - ``sale_price``: time-limited promo available to *all* shoppers
      ("in de aanbieding"), or ``None`` when there is none.
    - ``loyalty_price``: price requiring the store's loyalty card (AH
      Bonuskaart / Jumbo Extra's), or ``None`` when there is none.
    """

    supermarket: str
    store_name: str
    brand: str
    pack_size: str
    regular_price: float
    sale_price: float | None
    loyalty_price: float | None
