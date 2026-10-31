from sqlalchemy import or_, select

from assignment.db import engine, products


def search_products(query: str, max_price_cents: int = 100000) -> dict:
    """Search the seeded sports catalog. Prices are integer USD cents."""
    if len(query) > 200 or max_price_cents < 0:
        return {"status": "error", "message": "Invalid search parameters"}
    pattern = "%" + query.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    stmt = (
        select(products)
        .where(
            or_(
                products.c.name.ilike(pattern, escape="!"),
                products.c.category.ilike(pattern, escape="!"),
            ),
            products.c.price_cents <= max_price_cents,
        )
        .order_by(products.c.id)
        .limit(20)
    )
    with engine().connect() as conn:
        return {
            "status": "ok",
            "currency": "USD",
            "products": [dict(r) for r in conn.execute(stmt).mappings()],
        }


def get_product(product_id: str) -> dict:
    """Fetch authoritative price and stock for one product."""
    with engine().connect() as conn:
        row = conn.execute(select(products).where(products.c.id == product_id)).mappings().first()
        return {"status": "ok", "product": dict(row)} if row else {"status": "not_found"}
