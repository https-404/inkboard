import pytest


def _sample_blocks():
    return [
        {
            "type": "heading",
            "content": "Hello World",
            "metadata": {"level": 1},
        },
        {
            "type": "paragraph",
            "content": "This is a test article.",
        },
    ]


@pytest.mark.anyio
async def test_article_crud_flow(client):
    # Create user and login
    s = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "author@example.com",
            "username": "author",
            "password": "StrongPassw0rd!",
        },
    )
    assert s.status_code in (200, 201)
    l = await client.post(
        "/api/v1/auth/login",
        json={"email": "author@example.com", "password": "StrongPassw0rd!"},
    )
    assert l.status_code == 200
    tokens = l.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Create article (draft)
    create = await client.post(
        "/api/v1/articles",
        headers=headers,
        json={
            "title": "My First Article",
            "subtitle": "Intro",
            "content": _sample_blocks(),
            "tags": ["test", "intro"],
            "status": "draft",
        },
    )
    assert create.status_code == 201, create.text
    article = create.json()
    article_id = article["id"]

    # Get article by id (owner can view draft)
    get_owner = await client.get(f"/api/v1/articles/{article_id}", headers=headers)
    assert get_owner.status_code == 200
    assert get_owner.json()["title"] == "My First Article"

    # Update article to publish
    upd = await client.put(
        f"/api/v1/articles/{article_id}",
        headers=headers,
        json={"status": "published", "title": "My First Article (Edited)"},
    )
    assert upd.status_code == 200
    assert upd.json()["status"] in ("published", "draft", "archived")

    # List articles (public)
    lst = await client.get("/api/v1/articles")
    assert lst.status_code == 200
    assert isinstance(lst.json(), list)

    # Clap article
    clap = await client.post(
        f"/api/v1/articles/{article_id}/clap",
        headers=headers,
        json={"count": 3},
    )
    assert clap.status_code == 200
    assert clap.json()["count"] == 3

    # Delete article
    dele = await client.delete(f"/api/v1/articles/{article_id}", headers=headers)
    assert dele.status_code in (200, 204)


