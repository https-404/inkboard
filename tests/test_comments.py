import pytest


def _blocks():
    return [
        {"type": "paragraph", "content": "Post for comments"},
    ]


@pytest.mark.anyio
async def test_comment_lifecycle(client):
    # Author creates article
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "c1@example.com", "username": "c1", "password": "StrongPassw0rd!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "c1@example.com", "password": "StrongPassw0rd!"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    art = await client.post(
        "/api/v1/articles",
        headers=headers,
        json={"title": "Cmnt", "content": _blocks(), "status": "published"},
    )
    assert art.status_code == 201
    article_id = art.json()["id"]

    # Same user comments on the article
    create = await client.post(
        "/api/v1/comments",
        headers=headers,
        json={"article_id": article_id, "content": "Nice post!"},
    )
    assert create.status_code == 201
    comment = create.json()
    comment_id = comment["id"]

    # List article comments
    lst = await client.get(f"/api/v1/comments/article/{article_id}", headers=headers)
    assert lst.status_code == 200
    assert lst.json()["total"] >= 1

    # Update comment
    upd = await client.put(
        f"/api/v1/comments/{comment_id}",
        headers=headers,
        json={"content": "Edited comment"},
    )
    assert upd.status_code == 200
    assert upd.json()["content"] == "Edited comment"

    # React +1
    react = await client.post(
        f"/api/v1/comments/{comment_id}/react",
        headers=headers,
        json={"value": 1},
    )
    assert react.status_code == 200
    assert react.json()["value"] == 1

    # Delete comment
    dele = await client.delete(f"/api/v1/comments/{comment_id}", headers=headers)
    assert dele.status_code in (200, 204)


