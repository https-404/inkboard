import pytest


@pytest.mark.anyio
async def test_signup_then_login_flow(client):
    # Signup
    res = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "StrongPassw0rd!",
        },
    )
    assert res.status_code in (200, 201)

    # Duplicate signup should fail
    dup = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "StrongPassw0rd!",
        },
    )
    assert dup.status_code == 400

    # Login
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "StrongPassw0rd!"},
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["token_type"] == "bearer"
    assert "access_token" in tokens and "refresh_token" in tokens


@pytest.mark.anyio
async def test_login_invalid_credentials(client):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrong"},
    )
    assert login.status_code in (400, 401)


@pytest.mark.anyio
async def test_refresh_access_token_flow(client):
    # Create user and login
    signup = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "bob@example.com",
            "username": "bob",
            "password": "StrongPassw0rd!",
        },
    )
    assert signup.status_code in (200, 201)

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "StrongPassw0rd!"},
    )
    assert login.status_code == 200
    tokens = login.json()

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 200
    body = refresh.json()
    assert "access_token" in body


