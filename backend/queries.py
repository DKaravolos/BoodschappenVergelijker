"""Read-side database queries backing the API.

Every price the API returns is the *latest* Price Snapshot for a Listing. Since
snapshots are append-only (see ``docs/adr/0002``), the newest row per listing is
simply the one with the largest ``id`` -- ids are monotonic, so this avoids
having to parse/compare ISO timestamps to find "latest".
"""

import sqlite3

from backend.models import (
    Discount,
    ProductComparison,
    SUPERMARKETS,
    SupermarketListing,
    SupermarketStatus,
)

# The latest snapshot per listing: the row whose id is the max for that listing.
_LATEST_SNAPSHOT = """
    SELECT ps.*
    FROM price_snapshots ps
    JOIN (
        SELECT listing_id, MAX(id) AS max_id
        FROM price_snapshots
        GROUP BY listing_id
    ) latest ON ps.id = latest.max_id
"""


def _favourite_ids(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute("SELECT product_id FROM favourites").fetchall()
    return {r["product_id"] for r in rows}


def get_products(
    conn: sqlite3.Connection,
    q: str | None = None,
    brand: str | None = None,
) -> list[ProductComparison]:
    """Products with their latest per-Listing prices.

    ``q`` matches product name OR brand (case-insensitive substring). ``brand``
    filters to an exact brand (case-insensitive). Products with no matching
    Listing/price are still returned (empty ``listings``) so the compare table
    can show "not available" per Supermarket.
    """
    where: list[str] = []
    params: list[object] = []
    if q:
        where.append("(LOWER(p.name) LIKE ? OR LOWER(p.brand) LIKE ?)")
        needle = f"%{q.lower()}%"
        params += [needle, needle]
    if brand:
        where.append("LOWER(p.brand) = ?")
        params.append(brand.lower())

    clause = f"WHERE {' AND '.join(where)}" if where else ""
    product_rows = conn.execute(
        f"SELECT p.* FROM products p {clause} ORDER BY p.brand, p.name, p.pack_size",
        params,
    ).fetchall()

    favourites = _favourite_ids(conn)
    listings_by_product = _listings_by_product(conn)

    return [
        ProductComparison(
            id=row["id"],
            brand=row["brand"],
            name=row["name"],
            pack_size=row["pack_size"],
            is_favourite=row["id"] in favourites,
            listings=listings_by_product.get(row["id"], []),
        )
        for row in product_rows
    ]


def _listings_by_product(
    conn: sqlite3.Connection,
) -> dict[int, list[SupermarketListing]]:
    """Map product_id -> its Listings, each carrying its latest snapshot."""
    rows = conn.execute(
        f"""
        SELECT l.id AS listing_id, l.product_id, l.supermarket, l.store_name,
               l.store_url, s.scraped_at, s.regular_price, s.sale_price,
               s.loyalty_price
        FROM listings l
        JOIN ({_LATEST_SNAPSHOT}) s ON s.listing_id = l.id
        ORDER BY l.supermarket, l.store_name
        """
    ).fetchall()

    out: dict[int, list[SupermarketListing]] = {}
    for r in rows:
        out.setdefault(r["product_id"], []).append(
            SupermarketListing(
                listing_id=r["listing_id"],
                supermarket=r["supermarket"],
                store_name=r["store_name"],
                store_url=r["store_url"],
                scraped_at=r["scraped_at"],
                regular_price=r["regular_price"],
                sale_price=r["sale_price"],
                loyalty_price=r["loyalty_price"],
            )
        )
    return out


def get_brands(conn: sqlite3.Connection) -> list[str]:
    """Distinct brands, alphabetically, for the brand filter."""
    rows = conn.execute(
        "SELECT DISTINCT brand FROM products ORDER BY brand COLLATE NOCASE"
    ).fetchall()
    return [r["brand"] for r in rows]


def get_favourites(conn: sqlite3.Connection) -> list[ProductComparison]:
    """Favourite Products with the same shape as :func:`get_products`."""
    favourites = _favourite_ids(conn)
    if not favourites:
        return []
    return [p for p in get_products(conn) if p.id in favourites]


def add_favourite(conn: sqlite3.Connection, product_id: int) -> bool:
    """Mark a Product as favourite. Returns False if the Product doesn't exist."""
    exists = conn.execute(
        "SELECT 1 FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    if not exists:
        return False
    conn.execute(
        "INSERT OR IGNORE INTO favourites (product_id) VALUES (?)", (product_id,)
    )
    conn.commit()
    return True


def remove_favourite(conn: sqlite3.Connection, product_id: int) -> None:
    """Unmark a Product as favourite (no-op if it wasn't marked)."""
    conn.execute("DELETE FROM favourites WHERE product_id = ?", (product_id,))
    conn.commit()


def get_discounts(
    conn: sqlite3.Connection,
    supermarket: str | None = None,
) -> list[Discount]:
    """Listings whose latest snapshot has an active Sale or Loyalty price.

    Sorted by savings percentage, largest first. ``best_price`` is the lowest of
    the active discounted prices; ``savings``/``savings_pct`` compare it to the
    Regular Price.
    """
    rows = conn.execute(
        f"""
        SELECT l.id AS listing_id, l.product_id, l.supermarket, l.store_name,
               p.brand, p.name, p.pack_size, s.scraped_at, s.regular_price,
               s.sale_price, s.loyalty_price
        FROM listings l
        JOIN products p ON p.id = l.product_id
        JOIN ({_LATEST_SNAPSHOT}) s ON s.listing_id = l.id
        """
    ).fetchall()

    discounts: list[Discount] = []
    for r in rows:
        if supermarket and r["supermarket"] != supermarket:
            continue
        regular = r["regular_price"]
        active = [
            price
            for price in (r["sale_price"], r["loyalty_price"])
            if price is not None and price < regular
        ]
        if not active:
            continue
        best = min(active)
        savings = round(regular - best, 2)
        discounts.append(
            Discount(
                listing_id=r["listing_id"],
                product_id=r["product_id"],
                brand=r["brand"],
                name=r["name"],
                pack_size=r["pack_size"],
                supermarket=r["supermarket"],
                store_name=r["store_name"],
                scraped_at=r["scraped_at"],
                regular_price=regular,
                sale_price=r["sale_price"],
                loyalty_price=r["loyalty_price"],
                best_price=best,
                savings=savings,
                savings_pct=round(savings / regular * 100, 1) if regular else 0.0,
            )
        )

    discounts.sort(key=lambda d: d.savings_pct, reverse=True)
    return discounts


def get_scrape_status(conn: sqlite3.Connection) -> list[SupermarketStatus]:
    """Latest freshness + health per Supermarket.

    ``last_scraped_at`` is the newest snapshot timestamp for that Supermarket's
    Listings (i.e. when its data was last successfully captured); ``status`` and
    ``error_message`` come from that Supermarket's most recent ``scrape_runs``
    row so the UI can flag a failed refresh even when stale data remains.
    """
    last_scraped = {
        r["supermarket"]: r["last"]
        for r in conn.execute(
            """
            SELECT l.supermarket, MAX(s.scraped_at) AS last
            FROM listings l
            JOIN price_snapshots s ON s.listing_id = l.id
            GROUP BY l.supermarket
            """
        ).fetchall()
    }
    last_run = {
        r["supermarket"]: r
        for r in conn.execute(
            """
            SELECT sr.* FROM scrape_runs sr
            JOIN (
                SELECT supermarket, MAX(id) AS max_id
                FROM scrape_runs
                WHERE supermarket IS NOT NULL
                GROUP BY supermarket
            ) latest ON sr.id = latest.max_id
            """
        ).fetchall()
    }

    out: list[SupermarketStatus] = []
    for market in SUPERMARKETS:
        run = last_run.get(market)
        out.append(
            SupermarketStatus(
                supermarket=market,
                last_scraped_at=last_scraped.get(market),
                status=run["status"] if run else None,
                error_message=run["error_message"] if run else None,
            )
        )
    return out
