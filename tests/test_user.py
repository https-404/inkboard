import pytest


@pytest.mark.anyio
async def test_me_requires_auth(client):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401


@pytest.mark.anyio
async def test_me_with_token(client):
    # Create account and login
    s = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "meuser@example.com",
            "username": "meuser",
            "password": "StrongPassw0rd!",
        },
    )
    assert s.status_code in (200, 201)

    l = await client.post(
        "/api/v1/auth/login",
        json={"email": "meuser@example.com", "password": "StrongPassw0rd!"},
    )
    assert l.status_code == 200
    tokens = l.json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = await client.get("/api/v1/users/me", headers=headers)
    # Depending on profile defaults, service returns a profile; ensure success
    assert r.status_code == 200
    body = r.json()
    assert body.get("email") == "meuser@example.com"


