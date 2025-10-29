from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from minio.error import S3Error
from app.core.minio_client import minio_client
from app.core.config import settings
import io

media_router = APIRouter(prefix="/inkboard/storage", tags=["Media"])


@media_router.get("/{file_path:path}")
async def serve_file(file_path: str):
    """
    Serve files from MinIO storage.
    File path should be relative to bucket root (e.g., 'pfp/user-id.jpg').
    """
    try:
        # Get object from MinIO
        response = minio_client.get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=file_path,
        )
        
        # Read data into memory
        data = response.read()
        response.close()
        response.release_conn()
        
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if file_path.endswith((".jpg", ".jpeg")):
            content_type = "image/jpeg"
        elif file_path.endswith(".png"):
            content_type = "image/png"
        elif file_path.endswith(".webp"):
            content_type = "image/webp"
        elif file_path.endswith(".gif"):
            content_type = "image/gif"
        elif file_path.endswith(".svg"):
            content_type = "image/svg+xml"
        
        return StreamingResponse(
            io.BytesIO(data),
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=31536000",  # Cache for 1 year
            },
        )
    except S3Error as e:
        if e.code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve file: {str(e)}",
        )

