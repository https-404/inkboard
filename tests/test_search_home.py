import pytest


@pytest.mark.anyio
async def test_search_users(client):
    # create a couple of users
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "su1@example.com", "username": "sue", "password": "StrongPassw0rd!"},
    )
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "su2@example.com", "username": "sam", "password": "StrongPassw0rd!"},
    )

    r = await client.get("/api/v1/search/users", params={"q": "s", "limit": 10})
    assert r.status_code == 200
    body = r.json()
    assert "results" in body or "users" in body or "total" in body


@pytest.mark.anyio
async def test_home_public_and_private(client):
    # public trending
    r = await client.get("/api/v1/home/trending")
    assert r.status_code == 200

    # authenticated endpoints require token
    feed = await client.get("/api/v1/home/feed")
    assert feed.status_code == 401

    # create user and call feed/suggest
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "hf@example.com", "username": "hf", "password": "StrongPassw0rd!"},
    )
    l = await client.post(
        "/api/v1/auth/login",
        json={"email": "hf@example.com", "password": "StrongPassw0rd!"},
    )
    h = {"Authorization": f"Bearer {l.json()['access_token']}"}

    feed = await client.get("/api/v1/home/feed", headers=h)
    assert feed.status_code == 200
    suggest = await client.get("/api/v1/home/suggest-users", headers=h)
    assert suggest.status_code == 200


