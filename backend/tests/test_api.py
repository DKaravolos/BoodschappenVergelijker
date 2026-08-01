"""API tests for the read endpoints, favourites, and scrape status.

Each test seeds a throwaway SQLite DB directly (bypassing the not-yet-wired
scrape pipeline) so the endpoints are exercised against real rows.
"""

import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()
    _seed(database)
    return TestClient(app)


def _seed(db):
    """Two Products; Vivera stocked at AH (on loyalty) + Jumbo (on sale)."""
    with db.get_db() as conn:
        conn.executescript(
            """
            INSERT INTO products (id, brand, name, pack_size) VALUES
                (1, 'Vivera', 'Kipstukjes', '200g'),
                (2, 'Garden Gourmet', 'Schnitzel', '180g');

            INSERT INTO listings (id, product_id, supermarket, store_name) VALUES
                (1, 1, 'ah', 'Vivera Kipstukjes 200g'),
                (2, 1, 'jumbo', 'Vivera Kipstukjes'),
                (3, 2, 'ah', 'Garden Gourmet Schnitzel');

            -- Listing 1 (AH): older snapshot then newer one with a loyalty deal.
            INSERT INTO price_snapshots
                (listing_id, scraped_at, regular_price, sale_price, loyalty_price) VALUES
                (1, '2026-07-01T10:00:00', 2.99, NULL, NULL),
                (1, '2026-07-30T10:00:00', 2.99, NULL, 1.99),
                -- Listing 2 (Jumbo): on sale.
                (2, '2026-07-30T10:00:00', 2.79, 1.99, NULL),
                -- Listing 3 (AH): no discount.
                (3, '2026-07-30T10:00:00', 3.49, NULL, NULL);

            INSERT INTO scrape_runs (started_at, completed_at, supermarket, status) VALUES
                ('2026-07-30T09:00:00', '2026-07-30T09:01:00', 'ah', 'completed'),
                ('2026-07-30T09:00:00', '2026-07-30T09:01:00', 'jumbo', 'completed'),
                ('2026-07-30T09:00:00', NULL, 'vomar', 'failed');
            """
        )
        conn.commit()


def test_products_returns_latest_price_per_listing(client):
    resp = client.get("/products")
    assert resp.status_code == 200
    products = resp.json()
    assert len(products) == 2

    vivera = next(p for p in products if p["brand"] == "Vivera")
    ah = next(li for li in vivera["listings"] if li["supermarket"] == "ah")
    # Latest AH snapshot (loyalty deal), not the older plain one.
    assert ah["regular_price"] == 2.99
    assert ah["loyalty_price"] == 1.99
    assert ah["scraped_at"] == "2026-07-30T10:00:00"


def test_products_search_matches_name_and_brand(client):
    assert len(client.get("/products", params={"q": "kip"}).json()) == 1
    assert len(client.get("/products", params={"q": "vivera"}).json()) == 1
    assert len(client.get("/products", params={"q": "zzz"}).json()) == 0


def test_products_brand_filter(client):
    products = client.get("/products", params={"brand": "Vivera"}).json()
    assert [p["name"] for p in products] == ["Kipstukjes"]


def test_brands_endpoint(client):
    assert client.get("/brands").json() == ["Garden Gourmet", "Vivera"]


def test_discounts_sorted_by_savings_and_filtered(client):
    discounts = client.get("/discounts").json()
    # AH loyalty (2.99->1.99) and Jumbo sale (2.79->1.99); no Schnitzel deal.
    assert len(discounts) == 2
    assert discounts[0]["savings_pct"] >= discounts[1]["savings_pct"]

    jumbo = client.get("/discounts", params={"supermarket": "jumbo"}).json()
    assert len(jumbo) == 1
    assert jumbo[0]["best_price"] == 1.99
    assert jumbo[0]["sale_price"] == 1.99


def test_favourites_lifecycle(client):
    assert client.get("/favourites").json() == []

    assert client.post("/favourites/1").status_code == 204
    favs = client.get("/favourites").json()
    assert [p["id"] for p in favs] == [1]
    assert favs[0]["is_favourite"] is True

    # Idempotent add, then remove.
    assert client.post("/favourites/1").status_code == 204
    assert len(client.get("/favourites").json()) == 1
    assert client.delete("/favourites/1").status_code == 204
    assert client.get("/favourites").json() == []


def test_favourite_unknown_product_404(client):
    assert client.post("/favourites/999").status_code == 404


def test_scrape_status_reports_freshness_and_health(client):
    statuses = {s["supermarket"]: s for s in client.get("/scrape/status").json()}
    assert set(statuses) == {"ah", "jumbo", "vomar", "dekamarkt"}
    assert statuses["ah"]["last_scraped_at"] == "2026-07-30T10:00:00"
    assert statuses["ah"]["status"] == "completed"
    assert statuses["vomar"]["status"] == "failed"
    # Never scraped -> no data, no run.
    assert statuses["dekamarkt"]["last_scraped_at"] is None
    assert statuses["dekamarkt"]["status"] is None


def test_scrape_returns_status(client, monkeypatch):
    # Mock the scrapers so POST /scrape never touches the network.
    from backend.scrapers import ah, dekamarkt, jumbo, vomar

    async def empty():
        return []

    for module in (ah, jumbo, vomar, dekamarkt):
        monkeypatch.setattr(module, "scrape", empty)

    body = client.post("/scrape").json()
    assert body["status"] == "completed"
    assert len(body["statuses"]) == 4
