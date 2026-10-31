from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import select, update

from assignment import commerce
from assignment.catalog import get_product, search_products
from assignment.db import engine, orders, products, quotes


def quote(user="alice", quantity=2):
    result = commerce.create_quote(user, "BALL-001", quantity, "pickup")
    assert result["status"] == "confirmation_required"
    return result["quote"]["id"]


def test_confirmation_price_and_retry():
    quote_id = quote()
    assert (
        commerce.place_order("alice", quote_id, confirmed=False)["status"]
        == "confirmation_required"
    )
    assert get_product("BALL-001")["product"]["stock"] == 20
    first = commerce.place_order("alice", quote_id, confirmed=True)
    retry = commerce.place_order("alice", quote_id, confirmed=True)
    assert first["order"]["total_cents"] == 4998
    assert retry["order"]["id"] == first["order"]["id"]
    assert retry["replayed"]
    assert get_product("BALL-001")["product"]["stock"] == 18


def test_customer_isolation():
    quote_id = quote()
    assert commerce.place_order("bob", quote_id, confirmed=True)["status"] == "not_found"
    order = commerce.place_order("alice", quote_id, confirmed=True)["order"]
    assert commerce.get_order("bob", order["id"])["status"] == "not_found"
    assert commerce.update_delivery("bob", order["id"], "standard")["status"] == "not_found"
    assert commerce.update_delivery("alice", order["id"], "standard")["status"] == "ok"
    assert commerce.get_order("alice", order["id"])["order"]["delivery"] == "standard"


def test_expiry_and_invalid_input():
    for quantity in [0, -1, 101, True, 1.5]:
        assert commerce.create_quote("alice", "BALL-001", quantity, "pickup")["status"] == "error"
    assert commerce.create_quote("alice", "BALL-001", 1, "teleport")["status"] == "error"
    assert commerce.create_quote("alice", "RACKET-001", 1, "pickup")["status"] == "out_of_stock"
    quote_id = quote()
    with engine().begin() as conn:
        conn.execute(update(quotes).where(quotes.c.id == quote_id).values(expires_at=1))
    assert commerce.place_order("alice", quote_id, confirmed=True)["status"] == "expired"
    assert get_product("BALL-001")["product"]["stock"] == 20


def test_competing_orders_never_oversell():
    with engine().begin() as conn:
        conn.execute(update(products).where(products.c.id == "BALL-001").values(stock=1))
    ids = [quote("alice", 1), quote("bob", 1)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(commerce.place_order, user, q, confirmed=True)
            for user, q in zip(["alice", "bob"], ids)
        ]
        results = [future.result() for future in futures]
    assert sorted(r["status"] for r in results) == ["ok", "out_of_stock"]
    assert get_product("BALL-001")["product"]["stock"] == 0


def test_concurrent_retry_charges_stock_once():
    quote_id = quote()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(
            pool.map(lambda _: commerce.place_order("alice", quote_id, confirmed=True), range(4))
        )
    assert all(result["status"] == "ok" for result in results)
    assert len({result["order"]["id"] for result in results}) == 1
    assert get_product("BALL-001")["product"]["stock"] == 18
    with engine().connect() as conn:
        assert len(conn.execute(select(orders)).all()) == 1


def test_catalog_literal_search_and_budget():
    assert len(search_products("running", 9000)["products"]) == 1
    assert search_products("running", 8000)["products"] == []
    assert search_products("%' OR 1=1 --")["products"] == []
