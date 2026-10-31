"""Portable, transactional data access. No LLM-generated SQL is executed."""

from functools import lru_cache

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    event,
    insert,
    select,
)

from assignment.config import database_url

metadata = MetaData()
products = Table(
    "products",
    metadata,
    Column("id", String(40), primary_key=True),
    Column("name", String(200), nullable=False),
    Column("category", String(80), nullable=False),
    Column("price_cents", Integer, nullable=False),
    Column("stock", Integer, nullable=False),
    CheckConstraint("price_cents >= 0"),
    CheckConstraint("stock >= 0"),
)
quotes = Table(
    "quotes",
    metadata,
    Column("id", String(40), primary_key=True),
    Column("customer_id", String(200), nullable=False, index=True),
    Column("product_id", ForeignKey("products.id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price_cents", Integer, nullable=False),
    Column("delivery", String(20), nullable=False),
    Column("expires_at", Integer, nullable=False),
    CheckConstraint("quantity > 0"),
)
orders = Table(
    "orders",
    metadata,
    Column("id", String(40), primary_key=True),
    Column("quote_id", ForeignKey("quotes.id"), nullable=False, unique=True),
    Column("customer_id", String(200), nullable=False, index=True),
    Column("product_id", ForeignKey("products.id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("total_cents", Integer, nullable=False),
    Column("delivery", String(20), nullable=False),
    Column("status", String(20), nullable=False),
)
bugs = Table(
    "bugs",
    metadata,
    Column("id", String(40), primary_key=True),
    Column("title", String(200), nullable=False),
    Column("description", String(4000), nullable=False),
    Column("status", String(30), nullable=False),
    Column("severity", String(30), nullable=False),
    Column("file", String(200), nullable=False),
)


@lru_cache(maxsize=8)
def engine_for(url: str):
    kwargs = (
        {"connect_args": {"check_same_thread": False, "timeout": 30}}
        if url.startswith("sqlite")
        else {}
    )
    engine = create_engine(url, pool_pre_ping=True, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def sqlite_setup(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

    return engine


def engine():
    return engine_for(database_url())


def initialize() -> dict:
    """Idempotent explicit setup; run once before serving requests."""
    db = engine()
    metadata.create_all(db)
    with db.begin() as conn:
        existing = set(conn.execute(select(products.c.id)).scalars())
        for item in [
            {
                "id": "SHOE-001",
                "name": "Trail running shoes",
                "category": "running",
                "price_cents": 8999,
                "stock": 12,
            },
            {
                "id": "BALL-001",
                "name": "Match football",
                "category": "football",
                "price_cents": 2499,
                "stock": 20,
            },
            {
                "id": "MAT-001",
                "name": "Training yoga mat",
                "category": "fitness",
                "price_cents": 3500,
                "stock": 8,
            },
            {
                "id": "RACKET-001",
                "name": "Tournament racket",
                "category": "tennis",
                "price_cents": 12900,
                "stock": 0,
            },
        ]:
            if item["id"] not in existing:
                conn.execute(insert(products).values(**item))
        existing_bugs = set(conn.execute(select(bugs.c.id)).scalars())
        for bug in [
            {
                "id": "BUG-101",
                "title": "Checkout total ignores quantity",
                "description": "Buying three items charges for one. Reproduce: calculate_total(1200, 3) returns 1200, expected 3600.",
                "status": "open",
                "severity": "high",
                "file": "pricing.py",
            },
            {
                "id": "BUG-102",
                "title": "Empty cart causes division by zero",
                "description": "average_price([]) crashes instead of returning 0. Reproduce with an empty cart.",
                "status": "open",
                "severity": "medium",
                "file": "pricing.py",
            },
            {
                "id": "BUG-103",
                "title": "Negative quantities accepted",
                "description": "calculate_total(1200, -2) must reject invalid quantities with ValueError.",
                "status": "triaged",
                "severity": "high",
                "file": "pricing.py",
            },
        ]:
            if bug["id"] not in existing_bugs:
                conn.execute(insert(bugs).values(**bug))
    return {"status": "ready", "backend": db.dialect.name}
