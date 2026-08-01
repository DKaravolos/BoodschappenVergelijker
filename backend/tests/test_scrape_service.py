"""Tests for the scrape service: matching, storage, and partial failures.

Scrapers are monkeypatched to return canned items or raise, so nothing hits the
network.
"""

import pytest

from backend import database, scrape_service
from backend.scrapers import ah, dekamarkt, jumbo, vomar
from backend.scrapers.base import ScrapedItem, ScraperError


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    return database


def _item(supermarket, store_name, brand, pack, regular, sale=None, loyalty=None):
    return ScrapedItem(
        supermarket=supermarket,
        store_name=store_name,
        brand=brand,
        pack_size=pack,
        regular_price=regular,
        sale_price=sale,
        loyalty_price=loyalty,
    )


def _returns(items):
    async def scrape():
        return items
    return scrape


def _raises(message):
    async def scrape():
        raise ScraperError(message)
    return scrape


def _patch_all(monkeypatch, *, ah_items=None, jumbo_items=None, vomar_items=None,
               dekamarkt_items=None):
    monkeypatch.setattr(ah, "scrape", _returns(ah_items or []))
    monkeypatch.setattr(jumbo, "scrape", _returns(jumbo_items or []))
    monkeypatch.setattr(vomar, "scrape", _returns(vomar_items or []))
    monkeypatch.setattr(dekamarkt, "scrape", _returns(dekamarkt_items or []))


async def test_scrape_stores_products_listings_and_snapshots(db, monkeypatch):
    _patch_all(
        monkeypatch,
        ah_items=[_item("ah", "Vivera Kipstukjes 200g", "Vivera", "200g", 2.99, loyalty=1.99)],
        jumbo_items=[_item("jumbo", "Vivera Kipstukjes", "Vivera", "200 g", 2.79, sale=1.99)],
    )

    result = await scrape_service.run_scrape()

    assert result.status == "completed"
    with db.get_db() as conn:
        # The two Vivera Listings match to a single Product.
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM scrape_runs").fetchone()[0] == 4


async def test_partial_failure_records_status_and_keeps_others(db, monkeypatch):
    monkeypatch.setattr(ah, "scrape", _returns([
        _item("ah", "Vivera Kipstukjes 200g", "Vivera", "200g", 2.99),
    ]))
    monkeypatch.setattr(jumbo, "scrape", _returns([]))
    monkeypatch.setattr(vomar, "scrape", _raises("network down"))
    monkeypatch.setattr(dekamarkt, "scrape", _returns([]))

    result = await scrape_service.run_scrape()

    assert result.status == "partial"
    statuses = {s.supermarket: s for s in result.statuses}
    assert statuses["vomar"].status == "failed"
    assert statuses["vomar"].error_message == "network down"
    assert statuses["ah"].status == "completed"
    # AH data was still stored despite Vomar failing.
    with db.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 1


async def test_all_failing_is_failed_status(db, monkeypatch):
    for module in (ah, jumbo, vomar, dekamarkt):
        monkeypatch.setattr(module, "scrape", _raises("boom"))

    result = await scrape_service.run_scrape()

    assert result.status == "failed"
    with db.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0] == 0


async def test_rescrape_does_not_duplicate_listings_but_appends_snapshots(db, monkeypatch):
    _patch_all(
        monkeypatch,
        ah_items=[_item("ah", "Vivera Kipstukjes 200g", "Vivera", "200g", 2.99)],
    )

    await scrape_service.run_scrape("ah")
    await scrape_service.run_scrape("ah")

    with db.get_db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0] == 2


async def test_single_supermarket_target_only_scrapes_that_store(db, monkeypatch):
    _patch_all(
        monkeypatch,
        jumbo_items=[_item("jumbo", "Beyond Burger", "Beyond Meat", "226g", 4.49)],
    )

    result = await scrape_service.run_scrape("jumbo")

    assert result.status == "completed"
    with db.get_db() as conn:
        # Only one scrape_run row (jumbo), and only jumbo listings.
        runs = conn.execute("SELECT supermarket FROM scrape_runs").fetchall()
        assert [r["supermarket"] for r in runs] == ["jumbo"]
        assert conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 1
