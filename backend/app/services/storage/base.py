"""Abstract Storage Provider Interface.

Defines the pluggable storage contract for physical evidence binaries, generated
statutory pro-formas, compiled master dossiers, and offline ZIP export archives.
Supports interchangeable implementations (LocalStorageProvider, S3StorageProvider).
"""

from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import BinaryIO, Union


class StorageError(Exception):
    """Base exception for storage provider failures."""

    pass


class StorageFileNotFoundError(StorageError):
    """Raised when a requested file does not exist in storage."""

    pass


class StorageInvalidPathError(StorageError):
    """Raised when a path is malformed or attempts directory traversal."""

    pass


class StorageProvider(ABC):
    """Abstract base interface defining the storage provider contract."""

    @abstractmethod
    def save_file(self, stream: Union[BinaryIO, bytes], path: str) -> str:
        """Saves a binary file stream or raw bytes to the specified storage path.

        Args:
            stream: A readable binary file-like object or raw bytes.
            path: Relative target storage path (e.g. 'submissions/{id}/raw/{uuid}.pdf').

        Returns:
            The canonical stored path or identifier.

        Raises:
            StorageInvalidPathError: If path is unsafe or contains traversal sequences.
            StorageError: If the write operation fails.
        """
        pass

    @abstractmethod
    def get_file_stream(self, path: str) -> BinaryIO:
        """Retrieves an open readable binary stream of the file at the specified path.

        Args:
            path: Relative storage path of the file to read.

        Returns:
            A readable BinaryIO stream. Caller is responsible for closing the stream.

        Raises:
            StorageFileNotFoundError: If the file does not exist.
            StorageInvalidPathError: If path contains directory traversal sequences.
            StorageError: If an I/O error occurs while opening the stream.
        """
        pass

    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Deletes the file at the specified storage path.

        Args:
            path: Relative storage path of the file to delete.

        Returns:
            True if the file was deleted, False if the file did not exist.

        Raises:
            StorageInvalidPathError: If path contains directory traversal sequences.
            StorageError: If deletion fails due to an I/O or permissions error.
        """
        pass

    @abstractmethod
    def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """Generates an accessible URL or streaming route for the file.

        For local filesystem storage, returns the internal HTTP streaming route.
        For cloud object storage (S3, Cloudflare R2), returns a pre-signed GET URL.

        Args:
            path: Relative storage path of the file.
            expires_in: Expiration lifetime in seconds for pre-signed URLs (default: 3600).

        Returns:
            URL string for browser viewing or streaming.

        Raises:
            StorageFileNotFoundError: If the file does not exist.
            StorageInvalidPathError: If path contains directory traversal sequences.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks whether a file exists at the specified storage path.

        Args:
            path: Relative storage path.

        Returns:
            True if the file exists, False otherwise.
        """
        pass

    @abstractmethod
    def get_file_size(self, path: str) -> int:
        """Returns the size of the file in bytes.

        Args:
            path: Relative storage path.

        Returns:
            Integer byte size.

        Raises:
            StorageFileNotFoundError: If the file does not exist.
            StorageError: If size inspection fails.
        """
        pass

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Validates and sanitizes a relative storage path to prevent directory traversal.

        Args:
            path: Storage path string to validate.

        Returns:
            Sanitized POSIX-style path string.

        Raises:
            StorageInvalidPathError: If path is empty, absolute, or contains '..' traversal.
        """
        if not path or not path.strip():
            raise StorageInvalidPathError("Storage path cannot be empty.")

        cleaned = path.strip().replace("\\", "/")
        posix = PurePosixPath(cleaned)

        # Check for absolute paths (POSIX root or Windows drive letter)
        if (
            posix.is_absolute()
            or cleaned.startswith("/")
            or (len(cleaned) >= 2 and cleaned[1] == ":" and cleaned[0].isalpha())
        ):
            raise StorageInvalidPathError(
                f"Absolute storage paths are forbidden: '{path}'"
            )

        # Check for directory traversal
        parts = posix.parts
        if ".." in parts:
            raise StorageInvalidPathError(
                f"Directory traversal sequences ('..') are forbidden: '{path}'"
            )

        if "\x00" in cleaned:
            raise StorageInvalidPathError(
                "Null bytes are forbidden in storage paths."
            )

        return str(posix)
