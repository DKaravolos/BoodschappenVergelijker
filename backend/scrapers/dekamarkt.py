"""Dekamarkt scraper.

Dekamarkt is a Detailresult Groep webshop and runs on the shared platform
handled by ``detailresult.py``; this module only pins the store configuration
and exposes the standard ``scrape()`` entry point. Dekamarkt has no loyalty
programme, so every item's ``loyalty_price`` is None (folder promotions map to
``sale_price``).
"""

import asyncio

from backend.scrapers.base import ScrapedItem
from backend.scrapers.detailresult import _StoreConfig, scrape_store

_CONFIG = _StoreConfig(supermarket="dekamarkt", organization="dekamarkt")


async def scrape() -> list[ScrapedItem]:
    """Scrape Dekamarkt's vegetarian meat alternatives into ScrapedItems.

    Raises:
        ScraperError: on any HTTP/transport failure or malformed response.
    """
    return await scrape_store(_CONFIG)


if __name__ == "__main__":
    results = asyncio.run(scrape())
    print(f"Scraped {len(results)} Dekamarkt items")
    if results:
        print("First item:", results[0])
