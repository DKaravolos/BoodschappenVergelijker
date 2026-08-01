"""Jumbo scraper.

Uses Jumbo's unofficial mobile API (``mobileapi.jumbo.com``), the same backend
the Jumbo app talks to. No authentication is required for the product-search
endpoint; results are filtered on "vleesvervangers" (vegetarian meat
alternatives).

Price mapping (see ``ScrapedItem`` for the domain meaning of each field):

Jumbo's search response returns money as integer **cents**. Each product's
``prices`` block exposes ``price`` (the standard shelf price) and, when a promo
is running, ``promotionalPrice`` (the discounted price). Unlike AH -- whose
promotions run through the Bonuskaart -- Jumbo's shelf promotions ("1+1 gratis",
"2e halve prijs", "2 voor X") are available to *every* shopper, not just holders
of the Extra's card. So we map a Jumbo promotion to ``sale_price``:

- ``regular_price``  <- ``prices.price`` (cents -> euros)
- ``sale_price``     <- ``prices.promotionalPrice`` when it is a genuine discount
                        (present and below the regular price), else None
- ``loyalty_price``  <- always None

The classic search endpoint does not expose an Extra's-card-only unit price that
can be cleanly separated from an all-shopper promotion, so ``loyalty_price`` is
left None rather than guessed. Multi-buy promos that have no single discounted
unit price (``promotionalPrice`` absent) simply yield no sale price.
"""

import asyncio

import httpx

from backend.scrapers.base import ScrapedItem, ScraperError

_SEARCH_URL = "https://mobileapi.jumbo.com/v17/search"
_QUERY = "vleesvervangers"
_PAGE_SIZE = 100
_TIMEOUT = 20.0

_HEADERS = {
    # The mobile API rejects requests without an app-like User-Agent.
    "User-Agent": "Jumbo/8.19.1 (Android)",
    "Accept": "application/json",
}


def _cents_to_euros(cents: int | float | None) -> float | None:
    """Convert an integer-cents amount to euros, or None if absent."""
    if cents is None:
        return None
    return round(int(cents) / 100, 2)


def _to_item(product: dict) -> ScrapedItem | None:
    """Map one Jumbo search product onto a ScrapedItem, or None if unpriced."""
    prices = product.get("prices") or {}

    regular = _cents_to_euros(_amount(prices.get("price")))
    promo = _cents_to_euros(_amount(prices.get("promotionalPrice")))

    if regular is None:
        return None  # No usable shelf price -> not a valid listing.

    # A genuine all-shopper sale: promo present and below the shelf price.
    sale_price = promo if (promo is not None and promo < regular) else None

    return ScrapedItem(
        supermarket="jumbo",
        store_name=product.get("title", ""),
        brand=product.get("brand") or "",
        pack_size=product.get("quantity", ""),
        regular_price=regular,
        sale_price=sale_price,
        loyalty_price=None,
    )


def _amount(price_obj) -> int | float | None:
    """Pull the numeric ``amount`` out of a Jumbo price object.

    Jumbo wraps money as ``{"currency": "EUR", "amount": 279}``. Some fields
    are already bare numbers, so accept both shapes defensively.
    """
    if price_obj is None:
        return None
    if isinstance(price_obj, dict):
        return price_obj.get("amount")
    return price_obj


async def scrape() -> list[ScrapedItem]:
    """Scrape Jumbo's vegetarian meat alternatives into ScrapedItems.

    Raises:
        ScraperError: on any HTTP/transport failure or malformed response.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                _SEARCH_URL,
                params={"q": _QUERY, "offset": 0, "limit": _PAGE_SIZE},
                headers=_HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise ScraperError(f"Jumbo request failed: {exc}") from exc

    products = (data.get("products") or {}).get("data", [])
    items = [item for p in products if (item := _to_item(p)) is not None]
    return items


if __name__ == "__main__":
    results = asyncio.run(scrape())
    print(f"Scraped {len(results)} Jumbo items")
    if results:
        print("First item:", results[0])
