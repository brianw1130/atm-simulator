"""S3 client for snapshot and statement storage."""

import json
import logging
from typing import Any

from src.atm.config import settings

logger = logging.getLogger(__name__)


def _get_s3_client() -> Any | None:
    """Get boto3 S3 client.

    Returns None if boto3 is unavailable or the S3 bucket name is not configured.

    Returns:
        A boto3 S3 client, or None if S3 is not available.
    """
    if not settings.s3_bucket_name:
        return None
    try:
        import boto3

        return boto3.client("s3", region_name=settings.aws_region)
    except ImportError:
        logger.warning("boto3 not installed — S3 operations disabled.")
        return None


def upload_snapshot(data: dict[str, Any], filename: str) -> bool:
    """Upload JSON snapshot to S3.

    Args:
        data: Snapshot dict to serialize and upload.
        filename: The filename within the ``snapshots/`` prefix.

    Returns:
        True on success, False if S3 is not available.
    """
    client = _get_s3_client()
    if not client:
        return False
    key = f"snapshots/{filename}"
    client.put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json",
    )
    logger.info("Uploaded snapshot to s3://%s/%s", settings.s3_bucket_name, key)
    return True


def download_snapshot(key: str) -> dict[str, Any] | None:
    """Download JSON snapshot from S3.

    Args:
        key: The full S3 object key (e.g. ``snapshots/atm-snapshot-20240101.json``).

    Returns:
        Parsed snapshot dict, or None if S3 is not available or download fails.
    """
    client = _get_s3_client()
    if not client:
        return None
    response = client.get_object(Bucket=settings.s3_bucket_name, Key=key)
    result: dict[str, Any] = json.loads(response["Body"].read().decode("utf-8"))
    return result


def list_snapshots() -> list[str]:
    """List snapshot keys in S3.

    Returns:
        List of S3 object keys under the ``snapshots/`` prefix, or an empty list
        if S3 is not available.
    """
    client = _get_s3_client()
    if not client:
        return []
    response = client.list_objects_v2(
        Bucket=settings.s3_bucket_name,
        Prefix="snapshots/",
    )
    return [obj["Key"] for obj in response.get("Contents", [])]
