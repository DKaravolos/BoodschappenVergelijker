"""Resolve a scraped item to a Product (brand + fuzzy name matching).

See ``docs/adr/0001-product-matching-strategy.md``: we match on normalized Brand
and product name (fuzzy) rather than EAN codes. Pack size is part of Product
identity (``CONTEXT.md``) -- "Vivera Kipstukjes 200g" and "…400g" are distinct
Products -- so a match requires the *same* normalized brand **and** pack size,
plus a name similarity at or above the threshold.

``resolve_product`` returns an existing ``product_id`` when the item matches, or
creates a new Product and returns its id. Store-specific names (e.g. "Vivera
Kipstukjes 200g") are cleaned into a Product name ("Kipstukjes") by stripping the
brand and pack tokens before matching.
"""

import logging
import re
import sqlite3

from rapidfuzz import fuzz

from backend.scrapers.base import ScrapedItem

logger = logging.getLogger(__name__)

# Name similarity (0-100) at/above which two same-brand, same-pack Listings are
# treated as the same Product.
NAME_THRESHOLD = 85

# Size tokens like "200g", "200 g", "4 stuks", "0.5 l" left behind in a name.
_SIZE_RE = re.compile(
    r"\b\d+[.,]?\d*\s*(?:gram|kg|g|ml|l|liter|stuks?|st|x)\b",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _normalize_pack(pack: str) -> str:
    """Normalize a pack size so "200g" / "200 g" / "200 gram" compare equal."""
    p = _normalize(pack)
    p = re.sub(r"\bgram\b", "g", p)
    p = re.sub(r"\bliter\b", "l", p)
    p = re.sub(r"\bstuks?\b", "st", p)
    return p.replace(" ", "")


def _clean_name(store_name: str, brand: str, pack_size: str) -> str:
    """Derive a Product name from a store-specific name.

    Removes the brand and pack size (and any leftover size tokens), preserving
    the original casing so the stored name stays human-readable.
    """
    name = store_name
    if brand:
        name = re.sub(re.escape(brand), " ", name, flags=re.IGNORECASE)
    if pack_size:
        name = re.sub(re.escape(pack_size), " ", name, flags=re.IGNORECASE)
    name = _SIZE_RE.sub(" ", name)
    name = re.sub(r"\s+", " ", name).strip(" -,·")
    return name or store_name  # fall back if stripping removed everything


def resolve_product(conn: sqlite3.Connection, item: ScrapedItem) -> int:
    """Return the product_id for ``item``, creating a Product if none matches."""
    name = _clean_name(item.store_name, item.brand, item.pack_size)
    norm_name = _normalize(name)
    norm_brand = _normalize(item.brand)
    norm_pack = _normalize_pack(item.pack_size)

    rows = conn.execute("SELECT id, brand, name, pack_size FROM products").fetchall()
    for row in rows:
        if _normalize(row["brand"]) != norm_brand:
            continue
        if _normalize_pack(row["pack_size"]) != norm_pack:
            continue
        existing = _normalize(row["name"])
        if existing == norm_name or fuzz.token_sort_ratio(norm_name, existing) >= NAME_THRESHOLD:
            logger.debug(
                "matched %r -> product %d (%r)", item.store_name, row["id"], row["name"]
            )
            return row["id"]

    cur = conn.execute(
        "INSERT INTO products (brand, name, pack_size) VALUES (?, ?, ?)",
        (item.brand, name, item.pack_size),
    )
    product_id = int(cur.lastrowid)
    logger.debug("created product %d for %r (%r)", product_id, item.store_name, name)
    return product_id
