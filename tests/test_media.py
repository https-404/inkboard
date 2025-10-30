import io
import pytest


@pytest.mark.anyio
async def test_upload_article_image(monkeypatch, client):
    # Auth
    await client.post(
        "/api/v1/auth/signup",
        json={"email": "m1@example.com", "username": "m1", "password": "StrongPassw0rd!"},
    )
    l = await client.post(
        "/api/v1/auth/login",
        json={"email": "m1@example.com", "password": "StrongPassw0rd!"},
    )
    h = {"Authorization": f"Bearer {l.json()['access_token']}"}

    # Stub upload and storage URL
    async def fake_upload(file, user_id):
        return f"articles/{user_id}/fake.jpg"

    from app import services as app_services
    # monkeypatch the upload func directly on import path used by router
    import app.services.minio_service as minio_service
    monkeypatch.setattr(minio_service, "upload_article_image", fake_upload)

    # Also ensure get_storage_url returns deterministic URL
    monkeypatch.setattr(minio_service, "get_storage_url", lambda p: f"http://storage/{p}")

    # Send multipart upload
    files = {"image": ("test.jpg", io.BytesIO(b"fake-bytes"), "image/jpeg")}
    r = await client.post("/api/v1/articles/upload-image", headers=h, files=files)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["image_url"].startswith("http://storage/")
    assert body["image_path"].endswith("fake.jpg")


