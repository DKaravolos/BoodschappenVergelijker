"""Albert Heijn scraper.

Uses AH's unofficial mobile API (``api.ah.nl``). Access is granted via an
anonymous member token; product data comes from the mobile product-search
endpoint filtered on "vleesvervangers" (vegetarian meat alternatives).

Price mapping (see ``ScrapedItem`` for the domain meaning of each field):

AH's search response exposes only two price numbers per product --
``priceBeforeBonus`` (the standard shelf price) and ``currentPrice`` (the
active bonus price, present only during a promotion). It does NOT distinguish
a Bonuskaart-only price from an all-shoppers sale. AH's promotions run through
the Bonuskaart programme, so -- per the task's rule for a single bonus price --
we map:

- ``regular_price``  <- ``priceBeforeBonus`` (fallback ``currentPrice``)
- ``loyalty_price``  <- ``currentPrice`` when it is a genuine discount
                        (bonus active and below the regular price), else None
- ``sale_price``     <- always None (AH exposes no separate all-shoppers sale)

Multi-buy promos (e.g. "2 voor X") have ``currentPrice = None`` even though
``isBonus`` is true; there is no single unit bonus price to report, so
``loyalty_price`` stays None for those.
"""

import asyncio

import httpx

from backend.scrapers.base import ScrapedItem, ScraperError

_AUTH_URL = "https://api.ah.nl/mobile-auth/v1/auth/token/anonymous"
_SEARCH_URL = "https://api.ah.nl/mobile-services/product/search/v2"
_QUERY = "vleesvervangers"
_PAGE_SIZE = 100
_TIMEOUT = 20.0

_BASE_HEADERS = {
    "User-Agent": "Appie/8.22.3",
    "x-application": "AHWEBSHOP",
}


async def _get_anonymous_token(client: httpx.AsyncClient) -> str:
    """Fetch an anonymous bearer token required for all product calls."""
    resp = await client.post(_AUTH_URL, json={"clientId": "appie"}, headers=_BASE_HEADERS)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise ScraperError("AH auth response did not contain an access_token")
    return token


def _to_item(product: dict) -> ScrapedItem | None:
    """Map one AH search product onto a ScrapedItem, or None if unpriced."""
    current = product.get("currentPrice")
    before = product.get("priceBeforeBonus")

    # A genuine discount: bonus active with a current price below the shelf price.
    is_discount = (
        product.get("isBonus")
        and current is not None
        and before is not None
        and current < before
    )

    if is_discount:
        regular_price = before
        loyalty_price = current
    else:
        regular_price = before if before is not None else current
        loyalty_price = None

    if regular_price is None:
        return None  # No usable price -> not a valid listing.

    return ScrapedItem(
        supermarket="ah",
        store_name=product.get("title", ""),
        brand=product.get("brand") or "",
        pack_size=product.get("salesUnitSize", ""),
        regular_price=float(regular_price),
        sale_price=None,
        loyalty_price=float(loyalty_price) if loyalty_price is not None else None,
    )


async def scrape() -> list[ScrapedItem]:
    """Scrape AH's vegetarian meat alternatives into ScrapedItems.

    Raises:
        ScraperError: on any HTTP/transport failure or malformed response.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token = await _get_anonymous_token(client)
            headers = {**_BASE_HEADERS, "Authorization": f"Bearer {token}"}
            resp = await client.get(
                _SEARCH_URL,
                params={"query": _QUERY, "size": _PAGE_SIZE},
                headers=headers,
            )
            resp.raise_for_status()
            products = resp.json().get("products", [])
    except httpx.HTTPError as exc:
        raise ScraperError(f"AH request failed: {exc}") from exc

    items = [item for p in products if (item := _to_item(p)) is not None]
    return items


if __name__ == "__main__":
    results = asyncio.run(scrape())
    print(f"Scraped {len(results)} AH items")
    if results:
        print("First item:", results[0])
