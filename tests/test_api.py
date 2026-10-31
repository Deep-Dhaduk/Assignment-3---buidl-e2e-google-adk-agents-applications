import pytest
from fastapi.testclient import TestClient

from assignment.api import app

TOKEN = "test-only-token-abcdefghijklmnopqrstuvwxyz"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("APP_API_KEY", TOKEN)
    with TestClient(app) as client:
        yield client


def test_api_authentication(client):
    assert client.get("/health").status_code == 200
    assert client.get("/agents").status_code == 401
    assert client.get("/agents", headers={"Authorization": "Bearer incorrect"}).status_code == 401
    response = client.get("/agents", headers={"Authorization": "Bearer " + TOKEN})
    assert response.status_code == 200
    assert len(response.json()["agents"]) == 5


def test_api_checkout_and_input_validation(client):
    headers = {"Authorization": "Bearer " + TOKEN}
    payload = {"product_id": "SHOE-001", "quantity": 1, "delivery": "standard"}
    quote = client.post("/shop/quotes", headers=headers, json=payload).json()
    endpoint = "/shop/quotes/" + quote["quote"]["id"] + "/checkout"
    assert (
        client.post(endpoint, headers=headers, json={"confirmed": False}).json()["status"]
        == "confirmation_required"
    )
    first = client.post(endpoint, headers=headers, json={"confirmed": True}).json()
    second = client.post(endpoint, headers=headers, json={"confirmed": True}).json()
    assert first["order"]["id"] == second["order"]["id"]
    payload["quantity"] = -1
    assert client.post("/shop/quotes", headers=headers, json=payload).status_code == 422


def test_startup_rejects_missing_auth(monkeypatch):
    monkeypatch.delenv("APP_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="APP_API_KEY"):
        with TestClient(app):
            pass
