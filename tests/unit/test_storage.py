import io
from typing import BinaryIO, Union
import pytest

from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from app.services.storage.base import (
    StorageError,
    StorageFileNotFoundError,
    StorageInvalidPathError,
    StorageProvider,
)
from app.services.storage.local import LocalStorageProvider
from app.services.storage.s3 import S3StorageProvider


def test_storage_provider_cannot_be_instantiated_directly():
    """Verifies StorageProvider is an abstract class and cannot be instantiated."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        StorageProvider()


def test_storage_provider_incomplete_subclass_fails():
    """Verifies subclasses missing required abstract methods cannot be instantiated."""

    class IncompleteProvider(StorageProvider):
        def save_file(self, stream: Union[BinaryIO, bytes], path: str) -> str:
            return path

    with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteProvider with abstract method"):
        IncompleteProvider()


def test_storage_provider_complete_subclass_succeeds():
    """Verifies a fully implemented subclass satisfies the abstract contract."""

    class MockStorageProvider(StorageProvider):
        def __init__(self):
            self.files = {}

        def save_file(self, stream: Union[BinaryIO, bytes], path: str) -> str:
            clean_path = self.sanitize_path(path)
            content = stream if isinstance(stream, bytes) else stream.read()
            self.files[clean_path] = content
            return clean_path

        def get_file_stream(self, path: str) -> BinaryIO:
            clean_path = self.sanitize_path(path)
            if clean_path not in self.files:
                raise StorageFileNotFoundError(f"File not found: {clean_path}")
            return io.BytesIO(self.files[clean_path])

        def delete_file(self, path: str) -> bool:
            clean_path = self.sanitize_path(path)
            if clean_path in self.files:
                del self.files[clean_path]
                return True
            return False

        def get_file_url(self, path: str, expires_in: int = 3600) -> str:
            clean_path = self.sanitize_path(path)
            if clean_path not in self.files:
                raise StorageFileNotFoundError(f"File not found: {clean_path}")
            return f"/api/v1/evidence/stream/{clean_path}"

        def exists(self, path: str) -> bool:
            clean_path = self.sanitize_path(path)
            return clean_path in self.files

        def get_file_size(self, path: str) -> int:
            clean_path = self.sanitize_path(path)
            if clean_path not in self.files:
                raise StorageFileNotFoundError(f"File not found: {clean_path}")
            return len(self.files[clean_path])

    provider = MockStorageProvider()
    test_path = "submissions/sub-123/raw/cert.pdf"
    test_data = b"%PDF-1.4 test certificate content"

    # Save
    saved_path = provider.save_file(test_data, test_path)
    assert saved_path == test_path
    assert provider.exists(test_path)
    assert provider.get_file_size(test_path) == len(test_data)

    # Stream
    stream = provider.get_file_stream(test_path)
    assert stream.read() == test_data

    # URL
    url = provider.get_file_url(test_path)
    assert url == f"/api/v1/evidence/stream/{test_path}"

    # Delete
    assert provider.delete_file(test_path) is True
    assert provider.exists(test_path) is False
    assert provider.delete_file(test_path) is False

    # Missing file raises StorageFileNotFoundError
    with pytest.raises(StorageFileNotFoundError):
        provider.get_file_stream(test_path)

    with pytest.raises(StorageFileNotFoundError):
        provider.get_file_url(test_path)

    with pytest.raises(StorageFileNotFoundError):
        provider.get_file_size(test_path)


def test_sanitize_path_valid():
    """Verifies path normalization converts backslashes and preserves relative paths."""
    assert (
        StorageProvider.sanitize_path("submissions/123/raw/test.pdf")
        == "submissions/123/raw/test.pdf"
    )
    # Backslash conversion
    assert (
        StorageProvider.sanitize_path("submissions\\123\\generated\\doc.pdf")
        == "submissions/123/generated/doc.pdf"
    )
    # Redundant slashes
    assert (
        StorageProvider.sanitize_path("submissions//123///raw/file.pdf")
        == "submissions/123/raw/file.pdf"
    )


def test_sanitize_path_empty():
    """Verifies empty or whitespace-only paths are rejected."""
    with pytest.raises(StorageInvalidPathError, match="cannot be empty"):
        StorageProvider.sanitize_path("")

    with pytest.raises(StorageInvalidPathError, match="cannot be empty"):
        StorageProvider.sanitize_path("   ")


def test_sanitize_path_absolute_forbidden():
    """Verifies absolute paths are forbidden."""
    with pytest.raises(StorageInvalidPathError, match="Absolute storage paths are forbidden"):
        StorageProvider.sanitize_path("/var/data/submissions/test.pdf")

    with pytest.raises(StorageInvalidPathError, match="Absolute storage paths are forbidden"):
        StorageProvider.sanitize_path("C:/Windows/system32/cmd.exe")


def test_sanitize_path_directory_traversal_forbidden():
    """Verifies directory traversal sequences ('..') are strictly rejected."""
    with pytest.raises(StorageInvalidPathError, match="Directory traversal sequences"):
        StorageProvider.sanitize_path("../secret.key")

    with pytest.raises(StorageInvalidPathError, match="Directory traversal sequences"):
        StorageProvider.sanitize_path("submissions/../../etc/passwd")

    with pytest.raises(StorageInvalidPathError, match="Directory traversal sequences"):
        StorageProvider.sanitize_path("submissions/123/..\\..\\config.env")


def test_sanitize_path_null_bytes_forbidden():
    """Verifies paths containing null bytes are rejected."""
    with pytest.raises(StorageInvalidPathError, match="Null bytes are forbidden"):
        StorageProvider.sanitize_path("submissions/123/file\x00.pdf")


def test_storage_exception_hierarchy():
    """Verifies inheritance tree of custom storage exceptions."""
    assert issubclass(StorageError, Exception)
    assert issubclass(StorageFileNotFoundError, StorageError)
    assert issubclass(StorageInvalidPathError, StorageError)


# ==============================================================================
# LocalStorageProvider Test Suite
# ==============================================================================


def test_local_storage_provider_init(tmp_path):
    """Verifies LocalStorageProvider initializes and creates base_dir."""
    custom_dir = tmp_path / "custom_storage"
    assert not custom_dir.exists()

    provider = LocalStorageProvider(base_dir=custom_dir)
    assert custom_dir.exists()
    assert provider.base_dir == custom_dir.resolve()


def test_local_storage_save_bytes_and_get_stream(tmp_path):
    """Verifies saving raw bytes and reading back via binary stream."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    rel_path = "submissions/sub-001/raw/iso_13485.pdf"
    file_bytes = b"%PDF-1.7 statutory certificate data"

    # Save
    saved_path = provider.save_file(file_bytes, rel_path)
    assert saved_path == rel_path

    # Check physical file exists on disk
    expected_file = tmp_path / "submissions" / "sub-001" / "raw" / "iso_13485.pdf"
    assert expected_file.is_file()
    assert expected_file.read_bytes() == file_bytes

    # Stream
    stream = provider.get_file_stream(rel_path)
    try:
        assert stream.read() == file_bytes
    finally:
        stream.close()


def test_local_storage_save_stream_chunked(tmp_path):
    """Verifies saving from a file-like stream using chunked writes."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    rel_path = "submissions/sub-001/generated/covering_letter.pdf"

    # Create stream larger than default 64KB chunk size to test chunking
    large_data = b"X" * (1024 * 150)  # 150 KB
    stream_input = io.BytesIO(large_data)

    saved_path = provider.save_file(stream_input, rel_path)
    assert saved_path == rel_path
    assert provider.get_file_size(rel_path) == len(large_data)

    stream_out = provider.get_file_stream(rel_path)
    try:
        assert stream_out.read() == large_data
    finally:
        stream_out.close()


def test_local_storage_exists_and_get_file_size(tmp_path):
    """Verifies exists() and get_file_size() functionality."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    rel_path = "submissions/sub-002/assembled/master_dmf.pdf"
    content = b"PDF-DMF-BODY"

    assert provider.exists(rel_path) is False
    with pytest.raises(StorageFileNotFoundError, match="File not found in local storage"):
        provider.get_file_size(rel_path)

    provider.save_file(content, rel_path)
    assert provider.exists(rel_path) is True
    assert provider.get_file_size(rel_path) == len(content)


def test_local_storage_delete_file(tmp_path):
    """Verifies delete_file() removes the file from disk."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    rel_path = "submissions/sub-003/raw/temp.pdf"

    # Non-existent file returns False
    assert provider.delete_file(rel_path) is False

    # Save and verify
    provider.save_file(b"data", rel_path)
    assert provider.exists(rel_path) is True

    # Delete existing returns True
    assert provider.delete_file(rel_path) is True
    assert provider.exists(rel_path) is False

    # Subsequent delete returns False
    assert provider.delete_file(rel_path) is False


def test_local_storage_get_file_url(tmp_path):
    """Verifies get_file_url() returns relative streaming endpoint."""
    provider = LocalStorageProvider(base_dir=tmp_path)
    rel_path = "submissions/sub-004/raw/challan.pdf"

    with pytest.raises(StorageFileNotFoundError):
        provider.get_file_url(rel_path)

    provider.save_file(b"TR6-CHALLAN", rel_path)
    url = provider.get_file_url(rel_path)
    assert url == f"/api/v1/evidence/stream?path={rel_path}"


def test_local_storage_path_traversal_rejection(tmp_path):
    """Verifies LocalStorageProvider strictly rejects path traversal and escapes."""
    provider = LocalStorageProvider(base_dir=tmp_path)

    with pytest.raises(StorageInvalidPathError):
        provider.save_file(b"attack", "../escaped.txt")

    with pytest.raises(StorageInvalidPathError):
        provider.get_file_stream("../../etc/passwd")

    with pytest.raises(StorageInvalidPathError):
        provider.delete_file("submissions/../../../root.key")

    # exists() safely returns False without raising
    assert provider.exists("../non_existent.txt") is False


# ==============================================================================
# S3StorageProvider Test Suite
# ==============================================================================


def test_s3_storage_provider_init():
    """Verifies S3StorageProvider initializes with default and custom settings."""
    # Custom settings with injected mock client
    mock_client = MagicMock()
    provider = S3StorageProvider(
        bucket_name="custom-bucket",
        region_name="eu-central-1",
        endpoint_url="https://minio.local:9000",
        s3_client=mock_client,
    )
    assert provider.bucket_name == "custom-bucket"
    assert provider.region_name == "eu-central-1"
    assert provider.endpoint_url == "https://minio.local:9000"
    assert provider.client is mock_client


def test_s3_save_file_bytes():
    """Verifies saving raw bytes via put_object."""
    mock_client = MagicMock()
    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)

    test_path = "submissions/sub-100/raw/certificate.pdf"
    test_bytes = b"%PDF-1.4 s3 test content"

    saved_key = provider.save_file(test_bytes, test_path)
    assert saved_key == test_path

    mock_client.put_object.assert_called_once_with(
        Bucket="my-bucket",
        Key=test_path,
        Body=test_bytes,
    )


def test_s3_save_file_stream():
    """Verifies saving file-like streams via upload_fileobj."""
    mock_client = MagicMock()
    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)

    test_path = "submissions/sub-100/generated/dossier.pdf"
    stream = io.BytesIO(b"binary-stream-data")

    saved_key = provider.save_file(stream, test_path)
    assert saved_key == test_path

    mock_client.upload_fileobj.assert_called_once_with(
        Fileobj=stream,
        Bucket="my-bucket",
        Key=test_path,
    )


def test_s3_get_file_stream_success():
    """Verifies retrieving S3 object as a stream."""
    mock_client = MagicMock()
    mock_body = io.BytesIO(b"stored-s3-binary")
    mock_client.get_object.return_value = {"Body": mock_body}

    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)
    stream = provider.get_file_stream("submissions/sub-100/raw/file.pdf")

    assert stream.read() == b"stored-s3-binary"
    mock_client.get_object.assert_called_once_with(
        Bucket="my-bucket",
        Key="submissions/sub-100/raw/file.pdf",
    )


def test_s3_get_file_stream_not_found():
    """Verifies NoSuchKey raises StorageFileNotFoundError."""
    mock_client = MagicMock()
    mock_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )

    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)
    with pytest.raises(StorageFileNotFoundError, match="Object not found in S3 bucket"):
        provider.get_file_stream("submissions/sub-100/missing.pdf")


def test_s3_exists_and_get_file_size():
    """Verifies head_object logic for exists() and get_file_size()."""
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ContentLength": 1024}

    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)
    rel_path = "submissions/sub-100/raw/spec.pdf"

    assert provider.exists(rel_path) is True
    assert provider.get_file_size(rel_path) == 1024

    # When 404
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadObject",
    )
    assert provider.exists("submissions/sub-100/missing.pdf") is False
    with pytest.raises(StorageFileNotFoundError):
        provider.get_file_size("submissions/sub-100/missing.pdf")


def test_s3_delete_file():
    """Verifies delete_object logic and non-existent handling."""
    mock_client = MagicMock()
    # First file exists
    mock_client.head_object.return_value = {"ContentLength": 500}

    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)
    rel_path = "submissions/sub-100/raw/temp.pdf"

    assert provider.delete_file(rel_path) is True
    mock_client.delete_object.assert_called_once_with(
        Bucket="my-bucket",
        Key=rel_path,
    )

    # When file doesn't exist
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey"}},
        "HeadObject",
    )
    assert provider.delete_file("submissions/sub-100/non_existent.pdf") is False


def test_s3_get_file_url():
    """Verifies pre-signed URL generation and expiry handling."""
    mock_client = MagicMock()
    mock_client.head_object.return_value = {"ContentLength": 2048}
    mock_client.generate_presigned_url.return_value = (
        "https://my-bucket.s3.ap-south-1.amazonaws.com/test.pdf?X-Amz-Signature=xyz"
    )

    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)
    rel_path = "submissions/sub-100/raw/test.pdf"

    url = provider.get_file_url(rel_path, expires_in=1800)
    assert "https://my-bucket.s3.ap-south-1.amazonaws.com" in url

    mock_client.generate_presigned_url.assert_called_once_with(
        ClientMethod="get_object",
        Params={"Bucket": "my-bucket", "Key": rel_path},
        ExpiresIn=1800,
    )

    # When object not found
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404"}},
        "HeadObject",
    )
    with pytest.raises(StorageFileNotFoundError):
        provider.get_file_url("submissions/sub-100/missing.pdf")


def test_s3_path_traversal_rejection():
    """Verifies S3StorageProvider rejects path traversal and absolute paths."""
    mock_client = MagicMock()
    provider = S3StorageProvider(bucket_name="my-bucket", s3_client=mock_client)

    with pytest.raises(StorageInvalidPathError):
        provider.save_file(b"attack", "../evil.pdf")

    with pytest.raises(StorageInvalidPathError):
        provider.get_file_stream("/absolute/path.pdf")

    assert provider.exists("../secret.txt") is False



