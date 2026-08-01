import sqlite3

import pytest

from backend import database


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point the database module at a throwaway file for each test."""
    path = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", path)
    return path


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def test_init_db_creates_all_tables(db_path):
    database.init_db()
    with database.get_db() as conn:
        assert _table_names(conn) == {
            "products",
            "listings",
            "price_snapshots",
            "favourites",
            "scrape_runs",
        }


def test_init_db_creates_parent_directory(tmp_path, monkeypatch):
    nested = tmp_path / "data" / "test.db"
    monkeypatch.setattr(database, "DB_PATH", nested)
    database.init_db()
    assert nested.exists()


def test_init_db_is_idempotent(db_path):
    database.init_db()
    database.init_db()  # second run must not raise or duplicate schema
    with database.get_db() as conn:
        assert len(_table_names(conn)) == 5


def test_get_db_enforces_foreign_keys(db_path):
    database.init_db()
    with database.get_db() as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO price_snapshots (listing_id, scraped_at, regular_price) "
                "VALUES (999, '2026-08-01', 1.0)"
            )


def test_reset_db_clears_data(db_path):
    database.init_db()
    with database.get_db() as conn:
        conn.execute(
            "INSERT INTO products (brand, name, pack_size) VALUES ('Vivera', 'Kipstukjes', '200g')"
        )
        conn.commit()

    database.reset_db()

    with database.get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        assert count == 0
        assert len(_table_names(conn)) == 5
