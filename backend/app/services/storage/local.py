"""Local Filesystem Storage Provider.

Implements the StorageProvider interface writing files to the local disk under
the configured storage directory (e.g. ./storage/submissions/{id}/...).
Supports chunked binary streaming, parent directory auto-creation, and symlink
escape prevention.
"""

import os
from pathlib import Path
from typing import BinaryIO, Optional, Union

from app.core.config import settings
from app.services.storage.base import (
    StorageError,
    StorageFileNotFoundError,
    StorageInvalidPathError,
    StorageProvider,
)

DEFAULT_CHUNK_SIZE = 1024 * 64  # 64 KB chunk size for streaming writes


class LocalStorageProvider(StorageProvider):
    """Storage provider implementation for local filesystem persistence."""

    def __init__(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        """Initializes the LocalStorageProvider with a base directory.

        Args:
            base_dir: Root filesystem directory for storage. Defaults to settings.STORAGE_DIR.
        """
        if base_dir is None:
            self.base_dir = Path(settings.STORAGE_DIR).resolve()
        else:
            self.base_dir = Path(base_dir).resolve()

        os.makedirs(self.base_dir, exist_ok=True)

    def resolve_full_path(self, path: str) -> Path:
        """Resolves a relative storage path to an absolute Path and verifies it remains within base_dir.

        Args:
            path: Relative storage path.

        Returns:
            Resolved absolute Path object.

        Raises:
            StorageInvalidPathError: If path contains traversal sequences or escapes base_dir.
        """
        clean_path = self.sanitize_path(path)
        full_path = (self.base_dir / clean_path).resolve()

        # Strict containment check: ensure resolved path is inside base_dir
        try:
            full_path.relative_to(self.base_dir)
        except ValueError as exc:
            raise StorageInvalidPathError(
                f"Resolved storage path escapes base directory: '{path}'"
            ) from exc

        return full_path

    def save_file(self, stream: Union[BinaryIO, bytes], path: str) -> str:
        """Saves a binary file stream or raw bytes to disk under base_dir.

        Automatically creates any missing parent directories in the path hierarchy.

        Args:
            stream: A readable binary stream (supporting .read()) or raw bytes.
            path: Relative target storage path (e.g. 'submissions/{id}/raw/{uuid}.pdf').

        Returns:
            The canonical relative storage path.

        Raises:
            StorageInvalidPathError: If path is unsafe or attempts traversal.
            StorageError: If the file cannot be written.
        """
        full_path = self.resolve_full_path(path)
        clean_path = self.sanitize_path(path)

        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "wb") as f:
                if isinstance(stream, bytes):
                    f.write(stream)
                else:
                    # Write in chunks to prevent memory spikes on large PDF files
                    while True:
                        chunk = stream.read(DEFAULT_CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)

            return clean_path
        except (IOError, OSError) as exc:
            raise StorageError(
                f"Failed to write file to local storage at '{path}': {exc}"
            ) from exc

    def get_file_stream(self, path: str) -> BinaryIO:
        """Opens a binary readable stream for the file at the specified path.

        Args:
            path: Relative storage path.

        Returns:
            An open BinaryIO stream. The caller is responsible for closing the stream.

        Raises:
            StorageFileNotFoundError: If the file does not exist on disk.
            StorageInvalidPathError: If path is malformed.
            StorageError: If the file cannot be opened.
        """
        full_path = self.resolve_full_path(path)

        if not full_path.is_file():
            raise StorageFileNotFoundError(
                f"File not found in local storage: '{path}'"
            )

        try:
            return open(full_path, "rb")
        except (IOError, OSError) as exc:
            raise StorageError(
                f"Failed to open file stream at '{path}': {exc}"
            ) from exc

    def delete_file(self, path: str) -> bool:
        """Deletes a file from local storage if it exists.

        Args:
            path: Relative storage path.

        Returns:
            True if the file existed and was deleted, False if it did not exist.

        Raises:
            StorageInvalidPathError: If path is malformed.
            StorageError: If deletion fails due to an OS/permission error.
        """
        full_path = self.resolve_full_path(path)

        if not full_path.is_file():
            return False

        try:
            os.remove(full_path)
            return True
        except (IOError, OSError) as exc:
            raise StorageError(
                f"Failed to delete file from local storage at '{path}': {exc}"
            ) from exc

    def get_file_url(self, path: str, expires_in: int = 3600) -> str:
        """Returns the internal HTTP streaming endpoint route for the stored file.

        Args:
            path: Relative storage path.
            expires_in: Expiration lifetime (unused for local storage routes).

        Returns:
            Relative API streaming URL string.

        Raises:
            StorageFileNotFoundError: If the file does not exist on disk.
        """
        full_path = self.resolve_full_path(path)
        clean_path = self.sanitize_path(path)

        if not full_path.is_file():
            raise StorageFileNotFoundError(
                f"File not found in local storage: '{path}'"
            )

        return f"/api/v1/evidence/stream?path={clean_path}"

    def exists(self, path: str) -> bool:
        """Checks if a file exists on disk at the specified path.

        Args:
            path: Relative storage path.

        Returns:
            True if the file exists and is a regular file, False otherwise.
        """
        try:
            full_path = self.resolve_full_path(path)
            return full_path.is_file()
        except StorageInvalidPathError:
            return False

    def get_file_size(self, path: str) -> int:
        """Returns the size of the file in bytes.

        Args:
            path: Relative storage path.

        Returns:
            File size in bytes.

        Raises:
            StorageFileNotFoundError: If the file does not exist on disk.
            StorageError: If stat inspection fails.
        """
        full_path = self.resolve_full_path(path)

        if not full_path.is_file():
            raise StorageFileNotFoundError(
                f"File not found in local storage: '{path}'"
            )

        try:
            return full_path.stat().st_size
        except (IOError, OSError) as exc:
            raise StorageError(
                f"Failed to inspect file size for '{path}': {exc}"
            ) from exc
