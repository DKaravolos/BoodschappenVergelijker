"""Tests for product matching (brand + fuzzy name, pack size as identity)."""

import pytest

from backend import database, matching
from backend.scrapers.base import ScrapedItem


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    with database.get_db() as connection:
        yield connection


def _item(store_name, brand="Vivera", pack_size="200g", supermarket="ah"):
    return ScrapedItem(
        supermarket=supermarket,
        store_name=store_name,
        brand=brand,
        pack_size=pack_size,
        regular_price=2.99,
        sale_price=None,
        loyalty_price=None,
    )


def test_identical_brand_name_pack_resolve_to_same_product(conn):
    first = matching.resolve_product(conn, _item("Vivera Kipstukjes 200g", supermarket="ah"))
    second = matching.resolve_product(conn, _item("Vivera Kipstukjes 200g", supermarket="jumbo"))
    assert first == second
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1


def test_fuzzy_name_same_brand_and_pack_matches(conn):
    first = matching.resolve_product(conn, _item("Vivera Kipstukjes 200g"))
    # Slightly different store name, same brand + pack -> same Product.
    second = matching.resolve_product(conn, _item("Vivera Kip Stukjes", pack_size="200 g"))
    assert first == second
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1


def test_different_pack_size_is_distinct_product(conn):
    small = matching.resolve_product(conn, _item("Vivera Kipstukjes 200g", pack_size="200g"))
    large = matching.resolve_product(conn, _item("Vivera Kipstukjes 400g", pack_size="400g"))
    assert small != large
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 2


def test_different_brand_is_distinct_product(conn):
    a = matching.resolve_product(conn, _item("Kipstukjes", brand="Vivera"))
    b = matching.resolve_product(conn, _item("Kipstukjes", brand="Garden Gourmet"))
    assert a != b


def test_dissimilar_name_creates_new_product(conn):
    a = matching.resolve_product(conn, _item("Kipstukjes"))
    b = matching.resolve_product(conn, _item("Roomboter Amandelstaaf"))
    assert a != b
    assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 2


def test_stored_name_is_cleaned_and_readable(conn):
    matching.resolve_product(conn, _item("Vivera Kipstukjes 200g"))
    name = conn.execute("SELECT name FROM products").fetchone()["name"]
    assert name == "Kipstukjes"
