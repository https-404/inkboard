import pytest
from app.core.security import create_access_token


@pytest.mark.anyio
async def test_reports_endpoints(client):
    # Create a normal user and an article
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "r1@example.com", "username": "r1", "password": "StrongPassw0rd!"},
    )
    l = await client.post(
        "/api/v1/auth/login",
        json={"email": "r1@example.com", "password": "StrongPassw0rd!"},
    )
    h = {"Authorization": f"Bearer {l.json()['access_token']}"}
    art = await client.post(
        "/api/v1/articles",
        headers=h,
        json={"title": "Reportable", "content": [{"type": "paragraph", "content": "x"}], "status": "published"},
    )
    assert art.status_code == 201
    article_id = art.json()["id"]

    # Normal user creates a report
    cr = await client.post(
        "/api/v1/reports",
        headers=h,
        json={"article_id": article_id, "reason": "spam"},
    )
    assert cr.status_code == 201

    # Create an editor token (no DB lookup by middleware)
    editor_token = create_access_token(user_id="00000000-0000-0000-0000-000000000001", email="ed@example.com", username="ed", role="editor")
    he = {"Authorization": f"Bearer {editor_token}"}

    # List reports (editor)
    lr = await client.get("/api/v1/reports", headers=he)
    assert lr.status_code == 200
    data = lr.json()
    assert data["total"] >= 1

    # Moderate first report
    first = data["reports"][0]
    mod = await client.post(f"/api/v1/reports/{first['id']}/moderate", headers=he, json={"action": "approve", "note": "ok"})
    assert mod.status_code == 200
    assert mod.json()["status"] in ("approved", "rejected", "restored", "approve", "reject", "restore")


