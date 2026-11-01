import io
from typing import BinaryIO, Union
import pytest

from app.services.storage.base import (
    StorageError,
    StorageFileNotFoundError,
    StorageInvalidPathError,
    StorageProvider,
)


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

