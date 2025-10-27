import uuid
from datetime import timedelta
from minio.error import S3Error
from app.core.minio_client import minio_client
from app.core.config import settings


async def upload_file(file, folder: str = "uploads") -> str:
    """
    Upload a file-like object (from FastAPI UploadFile) to MinIO.
    Returns the object URL.
    """
    file_id = uuid.uuid4().hex
    object_name = f"{folder}/{file_id}_{file.filename}"

    try:
        result = minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type,
        )
        print(f"✅ Uploaded: {result.object_name}")
    except S3Error as e:
        print(f"❌ MinIO upload failed: {e}")
        raise

    return f"{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"


def get_presigned_url(object_name: str, expires_minutes: int = 10) -> str:
    """
    Generate a temporary pre-signed URL for secure file download.
    """
    url = minio_client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        expires=timedelta(minutes=expires_minutes),
    )
    return url
