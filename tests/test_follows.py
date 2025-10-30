import pytest


@pytest.mark.anyio
async def test_follow_unfollow_flow(client):
    # Create two users
    for i in (1, 2):
        await client.post(
            "/api/v1/auth/signup",
            json={
                "email": f"f{i}@example.com",
                "username": f"f{i}",
                "password": "StrongPassw0rd!",
            },
        )

    # Login user1 and fetch their id
    l1 = await client.post(
        "/api/v1/auth/login",
        json={"email": "f1@example.com", "password": "StrongPassw0rd!"},
    )
    h1 = {"Authorization": f"Bearer {l1.json()['access_token']}"}
    me1 = await client.get("/api/v1/users/me", headers=h1)
    user1_id = me1.json()["id"]

    # Login user2 and fetch their id
    l2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "f2@example.com", "password": "StrongPassw0rd!"},
    )
    h2 = {"Authorization": f"Bearer {l2.json()['access_token']}"}
    me2 = await client.get("/api/v1/users/me", headers=h2)
    user2_id = me2.json()["id"]

    # user1 follows user2
    follow = await client.post(f"/api/v1/follows/{user2_id}", headers=h1)
    assert follow.status_code == 200
    assert follow.json()["following"] is True

    # status check
    status = await client.get(f"/api/v1/follows/status/{user2_id}", headers=h1)
    assert status.status_code == 200
    assert status.json()["is_following"] is True

    # lists
    followers = await client.get(f"/api/v1/follows/followers/{user2_id}", headers=h2)
    assert followers.status_code == 200
    following = await client.get(f"/api/v1/follows/following/{user1_id}", headers=h1)
    assert following.status_code == 200

    # user1 unfollows user2
    unfollow = await client.delete(f"/api/v1/follows/{user2_id}", headers=h1)
    assert unfollow.status_code == 200
    assert unfollow.json()["following"] is False


