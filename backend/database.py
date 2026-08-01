import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "boodschappen.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY,
    brand       TEXT NOT NULL,
    name        TEXT NOT NULL,
    pack_size   TEXT NOT NULL,
    UNIQUE(brand, name, pack_size)
);

CREATE TABLE IF NOT EXISTS listings (
    id           INTEGER PRIMARY KEY,
    product_id   INTEGER REFERENCES products(id),
    supermarket  TEXT NOT NULL,
    store_name   TEXT NOT NULL,
    store_url    TEXT
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id             INTEGER PRIMARY KEY,
    listing_id     INTEGER REFERENCES listings(id),
    scraped_at     TEXT NOT NULL,
    regular_price  REAL NOT NULL,
    sale_price     REAL,
    loyalty_price  REAL
);

CREATE TABLE IF NOT EXISTS favourites (
    id          INTEGER PRIMARY KEY,
    product_id  INTEGER REFERENCES products(id) UNIQUE
);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id            INTEGER PRIMARY KEY,
    started_at    TEXT NOT NULL,
    completed_at  TEXT,
    supermarket   TEXT,
    status        TEXT NOT NULL,
    error_message TEXT
);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(_SCHEMA)


def reset_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            DROP TABLE IF EXISTS scrape_runs;
            DROP TABLE IF EXISTS favourites;
            DROP TABLE IF EXISTS price_snapshots;
            DROP TABLE IF EXISTS listings;
            DROP TABLE IF EXISTS products;
        """)
    init_db()
