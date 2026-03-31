"""S3 presigned URL routes for accessing stored artifacts."""

import boto3
from fastapi import APIRouter, HTTPException, Query

from app.config import get_settings

router = APIRouter(prefix="/storage", tags=["storage"])

# Allowed S3 key prefixes (prevent arbitrary bucket access)
ALLOWED_PREFIXES = ("processed/", "models/")


@router.get("/presign")
async def get_presigned_url(
    key: str = Query(..., description="S3 object key"),
    expires: int = Query(3600, ge=60, le=86400, description="URL expiry in seconds"),
):
    """Generate a presigned URL for an S3 object.

    Only allows access to keys under processed/ and models/ prefixes.
    """
    if not any(key.startswith(p) for p in ALLOWED_PREFIXES):
        raise HTTPException(403, "Access denied for this key prefix")

    settings = get_settings()

    try:
        s3 = boto3.client("s3", region_name=settings.aws_region)
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires,
        )
        return {"url": url, "key": key, "expires_in": expires}

    except Exception as e:
        raise HTTPException(502, f"Failed to generate presigned URL: {e}")
