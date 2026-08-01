"""Shared scraper backend for Vomar and Dekamarkt.

Vomar and Dekamarkt are both Detailresult Groep webshops and run on the same
e-commerce platform, so a single fetch + mapping implementation serves both --
the only per-store difference is which organisation the request is scoped to
(``_StoreConfig``) and the ``supermarket`` label written onto each item.

Neither chain has a loyalty programme (see ``CONTEXT.md``), so ``loyalty_price``
is always None. Folder promotions ("aanbieding") are available to every shopper
and therefore map to ``sale_price``:

- ``regular_price`` <- the standard shelf price
- ``sale_price``    <- the offer price when a promotion is active and below the
                       regular price, else None
- ``loyalty_price`` <- always None

NOTE ON THE ENDPOINT: the Detailresult product-search endpoint and JSON shape
below are a best-effort reconstruction of the platform's public webshop API.
The transport and price mapping are isolated (``_fetch_products`` / ``_to_item``)
so that the ScrapedItem contract stays covered by unit tests regardless of the
upstream schema; a single live run in a network-enabled environment is needed to
confirm the endpoint path and field names, which are the only things that would
change if the platform differs from what is encoded here.
"""

from dataclasses import dataclass

import httpx

from backend.scrapers.base import ScrapedItem, ScraperError

_BASE_URL = "https://api.detailresult.nl"
_SEARCH_PATH = "/products/product/search/vleesvervangers"
_PAGE_SIZE = 100
_TIMEOUT = 20.0

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; BoodschappenApp/0.1)",
    "Accept": "application/json",
}


@dataclass(frozen=True, slots=True)
class _StoreConfig:
    """Per-store parameters for the shared Detailresult platform."""

    supermarket: str  # ScrapedItem label: "vomar" | "dekamarkt"
    organization: str  # organisation id the platform scopes results to


def _first(product: dict, *keys: str):
    """Return the first present, non-None value among ``keys``.

    The platform is shared but the two storefronts have historically used
    slightly different casings for the same field; trying a few spellings keeps
    the mapper robust without duplicating it per store.
    """
    for key in keys:
        value = product.get(key)
        if value is not None:
            return value
    return None


def _to_item(product: dict, config: _StoreConfig) -> ScrapedItem | None:
    """Map one Detailresult product onto a ScrapedItem, or None if unpriced."""
    regular = _first(product, "NormalPrice", "normalPrice", "price")
    offer = _first(product, "OfferPrice", "offerPrice", "promotionPrice")

    if regular is None:
        return None  # No usable shelf price -> not a valid listing.

    regular = float(regular)
    offer = float(offer) if offer is not None else None

    # A genuine all-shopper sale: offer present and below the shelf price.
    sale_price = offer if (offer is not None and offer < regular) else None

    return ScrapedItem(
        supermarket=config.supermarket,
        store_name=_first(product, "Name", "name", "title") or "",
        brand=_first(product, "Brand", "brand") or "",
        pack_size=_first(product, "Packaging", "packaging", "salesUnitSize") or "",
        regular_price=regular,
        sale_price=sale_price,
        loyalty_price=None,
    )


async def _fetch_products(config: _StoreConfig) -> list[dict]:
    """Fetch the raw product list for a store from the Detailresult platform."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, base_url=_BASE_URL) as client:
            resp = await client.get(
                _SEARCH_PATH,
                params={"organization": config.organization, "size": _PAGE_SIZE},
                headers=_HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise ScraperError(f"{config.supermarket} request failed: {exc}") from exc

    # Accept either a bare list or a wrapper object with a products array.
    if isinstance(data, list):
        return data
    return _first(data, "Products", "products", "data") or []


async def scrape_store(config: _StoreConfig) -> list[ScrapedItem]:
    """Scrape one Detailresult store's vegetarian meat alternatives.

    Raises:
        ScraperError: on any HTTP/transport failure or malformed response.
    """
    products = await _fetch_products(config)
    return [item for p in products if (item := _to_item(p, config)) is not None]
