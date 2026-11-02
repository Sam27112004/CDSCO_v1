"""S3 / Object Storage Provider.

Implements the StorageProvider interface for Amazon S3, Cloudflare R2, MinIO,
or any S3-compliant object store. Supports pre-signed download URLs, multipart
streaming uploads, and custom endpoint overrides for local testing / private clouds.
"""

import io
from typing import Any, BinaryIO, Optional, Union

import boto3
import botocore
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.storage.base import (
    StorageError,
    StorageFileNotFoundError,
    StorageInvalidPathError,
    StorageProvider,
)


class S3StorageProvider(StorageProvider):
    """Storage provider for S3-compatible cloud object stores (AWS S3, MinIO, Cloudflare R2)."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        use_ssl: Optional[bool] = None,
        s3_client: Optional[Any] = None,
    ) -> None:
        """Initializes the S3StorageProvider.

        Args:
            bucket_name: Target S3 bucket name. Defaults to settings.S3_BUCKET_NAME.
            region_name: AWS region. Defaults to settings.S3_REGION_NAME.
            endpoint_url: Optional custom endpoint URL (for MinIO or Cloudflare R2).
            aws_access_key_id: Optional AWS access key ID.
            aws_secret_access_key: Optional AWS secret access key.
            use_ssl: Whether to use HTTPS. Defaults to settings.S3_USE_SSL.
            s3_client: Optional pre-configured boto3 client (useful for unit testing / mocking).
        """
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region_name = region_name or settings.S3_REGION_NAME
        self.endpoint_url = endpoint_url or settings.S3_ENDPOINT_URL
        self.aws_access_key_id = aws_access_key_id or settings.S3_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.S3_SECRET_ACCESS_KEY
        self.use_ssl = use_ssl if use_ssl is not None else settings.S3_USE_SSL

        if s3_client is not None:
            self.client = s3_client
        else:
            session = boto3.session.Session()
            client_kwargs = {
                "service_name": "s3",
                "region_name": self.region_name,
                "use_ssl": self.use_ssl,
                "config": botocore.client.Config(signature_version="s3v4"),
            }
            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url
            if self.aws_access_key_id and self.aws_secret_access_key:
                client_kwargs["aws_access_key_id"] = self.aws_access_key_id
                client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key

            self.client = session.client(**client_kwargs)

    def save_file(self, stream: Union[BinaryIO, bytes], path: str) -> str:
        """Uploads a binary stream or raw bytes to the S3 bucket.

        Args:
            stream: A readable binary file-like stream or raw bytes.
            path: Relative target storage key (e.g. 'submissions/{id}/raw/{uuid}.pdf').

        Returns:
            The canonical stored S3 object key.

        Raises:
            StorageInvalidPathError: If path contains invalid characters or traversal sequences.
            StorageError: If the S3 upload operation fails.
        """
        clean_path = self.sanitize_path(path)

        try:
            if isinstance(stream, bytes):
                self.client.put_object(
                    Bucket=self.bucket_name,
                    Key=clean_path,
                    Body=stream,
                )
            else:
                # Use upload_fileobj for automatic multi-part streaming on large files
                self.client.upload_fileobj(
                    Fileobj=stream,
                    Bucket=self.bucket_name,
                    Key=clean_path,
                )
            return clean_path
        except ClientError as exc:
            raise StorageError(
                f"S3 upload failed for key '{clean_path}' in bucket '{self.bucket_name}': {exc}"
            ) from exc
        except Exception as exc:
            raise StorageError(f"Unexpected error saving to S3: {exc}") from exc

    def get_file_stream(self, path: str) -> BinaryIO:
        """Retrieves a readable binary stream of the S3 object.

        Args:
            path: S3 object key.

        Returns:
            A readable BinaryIO stream.

        Raises:
            StorageFileNotFoundError: If the object does not exist in the bucket.
            StorageError: If retrieval fails.
        """
        clean_path = self.sanitize_path(path)

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=clean_path,
            )
            return response["Body"]
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ["404", "NoSuchKey", "NotFound"]:
                raise StorageFileNotFoundError(
                    f"Object not found in S3 bucket '{self.bucket_name}': '{clean_path}'"
                ) from exc
            raise StorageError(
                f"Failed to fetch S3 object '{clean_path}': {exc}"
            ) from exc

    def delete_file(self, path: str) -> bool:
        """Deletes an object from the S3 bucket.

        Args:
            path: S3 object key.

        Returns:
            True if the object existed and was deleted, False if it did not exist.

        Raises:
            StorageError: If deletion fails due to an S3 error.
        """
        clean_path = self.sanitize_path(path)

        if not self.exists(clean_path):
            return False

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=clean_path,
            )
            return True
        except ClientError as exc:
            raise StorageError(
                f"Failed to delete S3 object '{clean_path}': {exc}"
            ) from exc

    def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """Generates an expiring pre-signed URL for direct browser downloading / streaming.

        Args:
            path: S3 object key.
            expires_in: Expiration lifetime in seconds (default: 3600 / 1 hour).

        Returns:
            Pre-signed HTTPS GET URL string.

        Raises:
            StorageFileNotFoundError: If the object does not exist in S3.
            StorageError: If URL generation fails.
        """
        clean_path = self.sanitize_path(path)

        if not self.exists(clean_path):
            raise StorageFileNotFoundError(
                f"Object not found in S3 bucket '{self.bucket_name}': '{clean_path}'"
            )

        try:
            url = self.client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": clean_path,
                },
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as exc:
            raise StorageError(
                f"Failed to generate pre-signed URL for '{clean_path}': {exc}"
            ) from exc

    def exists(self, path: str) -> bool:
        """Checks whether an object exists in the S3 bucket using a lightweight HEAD request.

        Args:
            path: S3 object key.

        Returns:
            True if object exists, False otherwise.
        """
        try:
            clean_path = self.sanitize_path(path)
        except StorageInvalidPathError:
            return False

        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=clean_path,
            )
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ["404", "NoSuchKey", "NotFound"]:
                return False
            raise StorageError(
                f"S3 head_object error for key '{clean_path}': {exc}"
            ) from exc

    def get_file_size(self, path: str) -> int:
        """Returns the ContentLength byte size of the S3 object.

        Args:
            path: S3 object key.

        Returns:
            Object size in bytes.

        Raises:
            StorageFileNotFoundError: If the object does not exist in S3.
            StorageError: If head_object fails.
        """
        clean_path = self.sanitize_path(path)

        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=clean_path,
            )
            return int(response.get("ContentLength", 0))
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in ["404", "NoSuchKey", "NotFound"]:
                raise StorageFileNotFoundError(
                    f"Object not found in S3 bucket '{self.bucket_name}': '{clean_path}'"
                ) from exc
            raise StorageError(
                f"Failed to inspect size for S3 object '{clean_path}': {exc}"
            ) from exc

