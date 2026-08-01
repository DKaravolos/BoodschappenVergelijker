"""Unit tests for the Jumbo, Vomar, and Dekamarkt scrapers.

These tests never touch the network: each scraper's ``httpx.AsyncClient`` is
swapped for one backed by an ``httpx.MockTransport`` that returns a canned
response, so the ScrapedItem mapping (the part we actually own) is verified
deterministically.
"""

import httpx
import pytest

from backend.scrapers import dekamarkt, detailresult, jumbo, vomar
from backend.scrapers.base import ScraperError


def _mock_client(monkeypatch, module, handler):
    """Point ``module``'s httpx.AsyncClient at a MockTransport handler."""
    real_client_cls = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client_cls(*args, **kwargs)

    monkeypatch.setattr(module.httpx, "AsyncClient", factory)


def _json_responder(payload, status_code=200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=payload)

    return handler


# --------------------------------------------------------------------------- #
# Jumbo
# --------------------------------------------------------------------------- #

def _jumbo_payload(products):
    return {"products": {"data": products, "total": len(products)}}


@pytest.mark.asyncio
async def test_jumbo_maps_regular_price(monkeypatch):
    payload = _jumbo_payload([
        {
            "title": "Jumbo Vega Kipstukjes",
            "brand": "Jumbo",
            "quantity": "200 g",
            "prices": {"price": {"currency": "EUR", "amount": 279}},
        }
    ])
    _mock_client(monkeypatch, jumbo, _json_responder(payload))

    items = await jumbo.scrape()

    assert len(items) == 1
    item = items[0]
    assert item.supermarket == "jumbo"
    assert item.store_name == "Jumbo Vega Kipstukjes"
    assert item.brand == "Jumbo"
    assert item.pack_size == "200 g"
    assert item.regular_price == 2.79  # cents -> euros
    assert item.sale_price is None
    assert item.loyalty_price is None


@pytest.mark.asyncio
async def test_jumbo_active_promo_maps_to_sale_price(monkeypatch):
    payload = _jumbo_payload([
        {
            "title": "Vivera Kipstukjes",
            "brand": "Vivera",
            "quantity": "175 g",
            "prices": {
                "price": {"amount": 279},
                "promotionalPrice": {"amount": 199},
            },
        }
    ])
    _mock_client(monkeypatch, jumbo, _json_responder(payload))

    (item,) = await jumbo.scrape()

    assert item.regular_price == 2.79
    assert item.sale_price == 1.99  # all-shopper promo -> sale, not loyalty
    assert item.loyalty_price is None


@pytest.mark.asyncio
async def test_jumbo_ignores_promo_not_below_regular(monkeypatch):
    payload = _jumbo_payload([
        {
            "title": "Item",
            "prices": {"price": {"amount": 300}, "promotionalPrice": {"amount": 300}},
        }
    ])
    _mock_client(monkeypatch, jumbo, _json_responder(payload))

    (item,) = await jumbo.scrape()

    assert item.regular_price == 3.0
    assert item.sale_price is None


@pytest.mark.asyncio
async def test_jumbo_skips_unpriced_product(monkeypatch):
    payload = _jumbo_payload([
        {"title": "No price here", "prices": {}},
        {"title": "Priced", "prices": {"price": {"amount": 150}}},
    ])
    _mock_client(monkeypatch, jumbo, _json_responder(payload))

    items = await jumbo.scrape()

    assert [i.store_name for i in items] == ["Priced"]


@pytest.mark.asyncio
async def test_jumbo_empty_result(monkeypatch):
    _mock_client(monkeypatch, jumbo, _json_responder(_jumbo_payload([])))
    assert await jumbo.scrape() == []


@pytest.mark.asyncio
async def test_jumbo_http_error_raises_scraper_error(monkeypatch):
    _mock_client(monkeypatch, jumbo, _json_responder({}, status_code=503))
    with pytest.raises(ScraperError):
        await jumbo.scrape()


# --------------------------------------------------------------------------- #
# Vomar / Dekamarkt (shared Detailresult platform)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "module, label",
    [(vomar, "vomar"), (dekamarkt, "dekamarkt")],
)
@pytest.mark.asyncio
async def test_detailresult_maps_regular_price(monkeypatch, module, label):
    payload = {
        "Products": [
            {
                "Name": "Vivera Shoarma",
                "Brand": "Vivera",
                "Packaging": "150 g",
                "NormalPrice": 2.49,
            }
        ]
    }
    _mock_client(monkeypatch, detailresult, _json_responder(payload))

    (item,) = await module.scrape()

    assert item.supermarket == label
    assert item.store_name == "Vivera Shoarma"
    assert item.brand == "Vivera"
    assert item.pack_size == "150 g"
    assert item.regular_price == 2.49
    assert item.sale_price is None
    assert item.loyalty_price is None  # no loyalty programme


@pytest.mark.asyncio
async def test_detailresult_offer_maps_to_sale_price(monkeypatch):
    payload = {
        "Products": [
            {"Name": "Item", "NormalPrice": 3.0, "OfferPrice": 2.0, "IsOffer": True}
        ]
    }
    _mock_client(monkeypatch, detailresult, _json_responder(payload))

    (item,) = await vomar.scrape()

    assert item.regular_price == 3.0
    assert item.sale_price == 2.0
    assert item.loyalty_price is None


@pytest.mark.asyncio
async def test_detailresult_ignores_offer_not_below_regular(monkeypatch):
    payload = {"Products": [{"Name": "Item", "NormalPrice": 3.0, "OfferPrice": 3.5}]}
    _mock_client(monkeypatch, detailresult, _json_responder(payload))

    (item,) = await dekamarkt.scrape()

    assert item.sale_price is None


@pytest.mark.asyncio
async def test_detailresult_accepts_alternate_key_casing(monkeypatch):
    payload = {"products": [{"name": "Item", "normalPrice": 1.25}]}
    _mock_client(monkeypatch, detailresult, _json_responder(payload))

    (item,) = await vomar.scrape()

    assert item.store_name == "Item"
    assert item.regular_price == 1.25


@pytest.mark.asyncio
async def test_detailresult_accepts_bare_list_response(monkeypatch):
    payload = [{"Name": "Item", "NormalPrice": 1.0}]
    _mock_client(monkeypatch, detailresult, _json_responder(payload))

    items = await dekamarkt.scrape()

    assert len(items) == 1


@pytest.mark.asyncio
async def test_detailresult_skips_unpriced_product(monkeypatch):
    payload = {"Products": [{"Name": "No price"}, {"Name": "Priced", "NormalPrice": 1.0}]}
    _mock_client(monkeypatch, detailresult, _json_responder(payload))

    items = await vomar.scrape()

    assert [i.store_name for i in items] == ["Priced"]


@pytest.mark.asyncio
async def test_detailresult_http_error_raises_scraper_error(monkeypatch):
    _mock_client(monkeypatch, detailresult, _json_responder({}, status_code=500))
    with pytest.raises(ScraperError):
        await dekamarkt.scrape()
