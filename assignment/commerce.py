"""Order identity, confirmation, stock, and idempotency are enforced outside the model."""

import time
import uuid

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from assignment.db import engine, orders, products, quotes

DELIVERY_METHODS = {"standard", "pickup"}


def create_quote(customer_id: str, product_id: str, quantity: int, delivery: str) -> dict:
    if not customer_id or len(customer_id) > 200:
        return {"status": "error", "message": "A customer identity is required"}
    if type(quantity) is not int or not 1 <= quantity <= 100 or delivery not in DELIVERY_METHODS:
        return {
            "status": "error",
            "message": "Quantity must be 1–100; delivery must be standard or pickup",
        }
    with engine().begin() as conn:
        product = (
            conn.execute(select(products).where(products.c.id == product_id)).mappings().first()
        )
        if not product:
            return {"status": "not_found"}
        if product["stock"] < quantity:
            return {"status": "out_of_stock", "available": product["stock"]}
        quote = {
            "id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": product["price_cents"],
            "delivery": delivery,
            "expires_at": int(time.time()) + 900,
        }
        conn.execute(insert(quotes).values(**quote))
        return {
            "status": "confirmation_required",
            "quote": quote,
            "total_cents": product["price_cents"] * quantity,
            "currency": "USD",
        }


def place_order(customer_id: str, quote_id: str, *, confirmed: bool) -> dict:
    if confirmed is not True:
        return {
            "status": "confirmation_required",
            "message": "Confirm the displayed quote before purchase",
        }
    try:
        with engine().begin() as conn:
            quote = (
                conn.execute(
                    select(quotes)
                    .where(quotes.c.id == quote_id, quotes.c.customer_id == customer_id)
                    .with_for_update()
                )
                .mappings()
                .first()
            )
            if not quote:
                return {"status": "not_found"}
            previous = (
                conn.execute(select(orders).where(orders.c.quote_id == quote_id)).mappings().first()
            )
            if previous:
                return {"status": "ok", "order": dict(previous), "replayed": True}
            if quote["expires_at"] <= int(time.time()):
                return {"status": "expired", "message": "Request a new quote"}
            result = conn.execute(
                update(products)
                .where(products.c.id == quote["product_id"], products.c.stock >= quote["quantity"])
                .values(stock=products.c.stock - quote["quantity"])
            )
            if result.rowcount != 1:
                return {"status": "out_of_stock"}
            order = {
                "id": str(uuid.uuid4()),
                "quote_id": quote_id,
                "customer_id": customer_id,
                "product_id": quote["product_id"],
                "quantity": quote["quantity"],
                "total_cents": quote["unit_price_cents"] * quote["quantity"],
                "delivery": quote["delivery"],
                "status": "placed",
            }
            conn.execute(insert(orders).values(**order))
            return {"status": "ok", "order": order, "replayed": False}
    except IntegrityError:
        # A competing request may have committed the same quote. The losing
        # transaction (including its stock decrement) has rolled back here.
        with engine().connect() as conn:
            previous = (
                conn.execute(
                    select(orders).where(
                        orders.c.quote_id == quote_id, orders.c.customer_id == customer_id
                    )
                )
                .mappings()
                .first()
            )
            if previous:
                return {"status": "ok", "order": dict(previous), "replayed": True}
        raise


def get_order(customer_id: str, order_id: str) -> dict:
    with engine().connect() as conn:
        row = (
            conn.execute(
                select(orders).where(orders.c.id == order_id, orders.c.customer_id == customer_id)
            )
            .mappings()
            .first()
        )
        return {"status": "ok", "order": dict(row)} if row else {"status": "not_found"}


def update_delivery(customer_id: str, order_id: str, delivery: str) -> dict:
    if delivery not in DELIVERY_METHODS:
        return {"status": "error", "message": "Use standard or pickup"}
    with engine().begin() as conn:
        result = conn.execute(
            update(orders)
            .where(
                orders.c.id == order_id,
                orders.c.customer_id == customer_id,
                orders.c.status == "placed",
            )
            .values(delivery=delivery)
        )
        return {"status": "ok" if result.rowcount == 1 else "not_found"}
