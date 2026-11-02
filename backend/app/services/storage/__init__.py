"""Pluggable Storage Provider package."""

from app.core.config import settings
from app.services.storage.base import (
    StorageError,
    StorageFileNotFoundError,
    StorageInvalidPathError,
    StorageProvider,
)
from app.services.storage.local import LocalStorageProvider
from app.services.storage.s3 import S3StorageProvider
from app.services.storage.checksum import (
    ChecksumError,
    ChecksumMismatchError,
    HashingReader,
    calculate_sha256,
    verify_sha256,
)


def get_storage_provider() -> StorageProvider:
    """FastAPI dependency yielding the configured StorageProvider implementation."""
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageProvider(
            bucket_name=settings.S3_BUCKET_NAME,
            region_name=settings.S3_REGION_NAME,
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            use_ssl=settings.S3_USE_SSL,
        )
    return LocalStorageProvider(base_dir=settings.STORAGE_DIR)


__all__ = [
    "StorageProvider",
    "LocalStorageProvider",
    "S3StorageProvider",
    "StorageError",
    "StorageFileNotFoundError",
    "StorageInvalidPathError",
    "ChecksumError",
    "ChecksumMismatchError",
    "HashingReader",
    "calculate_sha256",
    "verify_sha256",
    "get_storage_provider",
]




