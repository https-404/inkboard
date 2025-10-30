import pytest


@pytest.mark.anyio
async def test_health_ok(client):
    r = await client.get("/api/v1/health/")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


@pytest.mark.anyio
async def test_health_db_ok(client):
    r = await client.get("/api/v1/health/db")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


