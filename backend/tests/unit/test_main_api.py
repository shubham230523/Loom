import pytest
from backend.app.main import app

@pytest.mark.asyncio
async def test_main_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["app"] == "Loom API"

@pytest.mark.asyncio
async def test_main_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
