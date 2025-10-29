import uuid
import io
from datetime import timedelta
from typing import Optional
from minio.error import S3Error
from fastapi import UploadFile, HTTPException, status
from PIL import Image
from app.core.minio_client import minio_client
from app.core.config import settings


# Allowed image types and max file size (5MB)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def compress_image(image: Image.Image, max_size: tuple[int, int] = (800, 800), quality: int = 85) -> bytes:
    """
    Compress image while maintaining aspect ratio.
    Returns compressed image as bytes.
    """
    # Resize if needed while maintaining aspect ratio
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Convert to RGB if necessary (for JPEG)
    if image.mode in ("RGBA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
        image = background
    
    # Save to bytes
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=quality, optimize=True)
    output.seek(0)
    return output.read()


async def upload_file(file: UploadFile, folder: str = "uploads") -> str:
    """
    Upload a file-like object (from FastAPI UploadFile) to MinIO.
    Returns the object path (not full URL) relative to bucket.
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

    # Return just the object path, not full URL
    return object_name


async def upload_pfp(file: UploadFile, user_id: str) -> str:
    """
    Upload and compress profile picture to MinIO.
    Returns the object path (pfp/{user_id}.jpg).
    
    Args:
        file: Uploaded file
        user_id: User UUID as string
        
    Returns:
        Object path like "pfp/{user_id}.jpg"
    """
    # Validate file type
    content_type = file.content_type.lower() if file.content_type else ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_IMAGE_TYPES))}"
        )
    
    # Validate file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {MAX_FILE_SIZE / (1024*1024):.0f}MB limit"
        )
    
    # Open and compress image
    try:
        image = Image.open(io.BytesIO(contents))
        compressed_data = compress_image(image)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Upload to MinIO
    object_name = f"pfp/{user_id}.jpg"
    
    try:
        minio_client.put_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_name,
            data=io.BytesIO(compressed_data),
            length=len(compressed_data),
            content_type="image/jpeg",
        )
        print(f"✅ Uploaded PFP: {object_name}")
    except S3Error as e:
        print(f"❌ MinIO upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )
    
    return object_name


async def delete_file(object_name: str) -> bool:
    """
    Delete a file from MinIO.
    Returns True if successful, False if file doesn't exist.
    """
    try:
        minio_client.remove_object(settings.MINIO_BUCKET_NAME, object_name)
        print(f"✅ Deleted: {object_name}")
        return True
    except S3Error as e:
        print(f"❌ Failed to delete {object_name}: {e}")
        return False


def get_storage_url(object_path: str) -> str:
    """
    Build storage URL using server base URL.
    Returns: http://{SERVER_URL}/api/v1/inkboard/storage/{object_path}
    """
    return f"{settings.SERVER_URL}/api/v1/inkboard/storage/{object_path}"


def get_presigned_url(object_name: str, expires_minutes: int = 10) -> str:
    """
    Generate a temporary pre-signed URL for secure file download.
    """
    url = minio_client.presigned_get_object(
        bucket_name=settings.MINIO_BUCKET_NAME,
        object_name=object_name,
        expires=timedelta(minutes=expires_minutes),
    )
    return url
