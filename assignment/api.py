"""Authenticated single-operator API. The development ADK UI stays local."""

import asyncio
import logging
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from assignment import commerce
from assignment.db import initialize
from assignment.runtime import AGENTS, run_turn

logger = logging.getLogger("assignment.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if len(os.getenv("APP_API_KEY", "")) < 24:
        raise RuntimeError("Set APP_API_KEY to a random secret of at least 24 characters")
    initialize()
    app.state.run_lock = asyncio.Lock()
    yield


app = FastAPI(title="ADK Assignment Suite", version="0.1.0", lifespan=lifespan)


def identity(authorization: str = Header(default="")) -> str:
    expected = os.getenv("APP_API_KEY", "")
    if len(expected) < 24 or not secrets.compare_digest(authorization, "Bearer " + expected):
        raise HTTPException(status_code=401, detail="Valid bearer token required")
    # Never accept customer_id or user_id from an LLM or HTTP body.
    return "operator"


class Turn(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    session_id: str | None = Field(default=None, max_length=100)
    project: Literal["buggy", "fixed"] = "buggy"


class Confirmation(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    confirmation_id: str = Field(min_length=1, max_length=200)
    confirmed: bool


async def dispatch(name: str, user_id: str, **kwargs) -> dict:
    if name not in AGENTS:
        raise HTTPException(404, "Unknown agent")
    # Serialize access to shared ADK toolsets and sessions in this single-worker service.
    if app.state.run_lock.locked():
        raise HTTPException(429, "An agent run is already active; retry after it finishes")
    request_id = str(uuid.uuid4())
    start = time.monotonic()
    async with app.state.run_lock:
        try:
            result = await run_turn(name, user_id, **kwargs)
            return {"request_id": request_id, **result}
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except TimeoutError as exc:
            raise HTTPException(504, "Agent run timed out") from exc
        except Exception as exc:
            # Do not log user content, model outputs, credentials, or exception text.
            logger.error("agent_failed request_id=%s type=%s", request_id, type(exc).__name__)
            raise HTTPException(
                502,
                {
                    "message": "Agent execution failed; inspect local configuration",
                    "request_id": request_id,
                },
            ) from exc
        finally:
            logger.info(
                "agent_run request_id=%s agent=%s seconds=%.3f",
                request_id,
                name,
                time.monotonic() - start,
            )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/agents")
def list_agents(user_id: str = Depends(identity)):
    return {"agents": AGENTS}


@app.post("/agents/{name}/run")
async def run(name: str, body: Turn, user_id: str = Depends(identity)):
    return await dispatch(name, user_id, **body.model_dump())


@app.post("/agents/{name}/confirm")
async def confirm(name: str, body: Confirmation, user_id: str = Depends(identity)):
    return await dispatch(name, user_id, **body.model_dump())


class QuoteInput(BaseModel):
    product_id: str = Field(min_length=1, max_length=40)
    quantity: int = Field(strict=True, ge=1, le=100)
    delivery: Literal["standard", "pickup"]


class CheckoutInput(BaseModel):
    confirmed: bool


@app.post("/shop/quotes")
def quote(body: QuoteInput, user_id: str = Depends(identity)):
    return commerce.create_quote(user_id, **body.model_dump())


@app.post("/shop/quotes/{quote_id}/checkout")
def checkout(quote_id: str, body: CheckoutInput, user_id: str = Depends(identity)):
    return commerce.place_order(user_id, quote_id, confirmed=body.confirmed)


@app.get("/shop/orders/{order_id}")
def order(order_id: str, user_id: str = Depends(identity)):
    return commerce.get_order(user_id, order_id)
