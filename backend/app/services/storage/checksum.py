"""Cryptographic Checksum Utilities.

Provides streaming SHA-256 checksum calculation, verification, and tamper
detection for incoming evidence files, generated pro-formas, and compiled dossiers.
Adheres to 21 CFR Part 11 and MDR 2017 data integrity requirements.
"""

import hashlib
import hmac
import io
from pathlib import Path
from typing import BinaryIO, Optional, Union

DEFAULT_HASH_CHUNK_SIZE = 1024 * 64  # 64 KB chunks


class ChecksumError(Exception):
    """Base exception for checksum failures."""

    pass


class ChecksumMismatchError(ChecksumError):
    """Raised when an inspected checksum does not match expected digest."""

    pass


def calculate_sha256(
    source: Union[BinaryIO, bytes, Path, str],
    chunk_size: int = DEFAULT_HASH_CHUNK_SIZE,
) -> str:
    """Calculates the SHA-256 hexadecimal checksum of a binary stream, bytes, or file path.

    If source is a seekable stream, its file pointer is rewound to its original
    position after hashing so subsequent consumers can read it without data loss.

    Args:
        source: Binary stream, raw bytes, or filesystem path.
        chunk_size: Buffer chunk size in bytes (default: 64 KB).

    Returns:
        64-character lowercase hexadecimal SHA-256 string.

    Raises:
        FileNotFoundError: If a file path is provided and does not exist.
        TypeError: If source type is unsupported.
    """
    hasher = hashlib.sha256()

    if isinstance(source, bytes):
        hasher.update(source)
        return hasher.hexdigest()

    if isinstance(source, (str, Path)):
        file_path = Path(source)
        if not file_path.is_file():
            raise FileNotFoundError(
                f"File not found for checksum calculation: {file_path}"
            )
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    if hasattr(source, "read"):
        initial_pos: Optional[int] = None
        if hasattr(source, "seek") and hasattr(source, "tell"):
            try:
                if hasattr(source, "seekable") and source.seekable():
                    initial_pos = source.tell()
                elif not hasattr(source, "seekable"):
                    initial_pos = source.tell()
            except (io.UnsupportedOperation, OSError):
                initial_pos = None

        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            hasher.update(chunk)

        if initial_pos is not None:
            source.seek(initial_pos)

        return hasher.hexdigest()

    raise TypeError(
        f"Unsupported source type for SHA-256 calculation: {type(source)}"
    )


def verify_sha256(
    source: Union[BinaryIO, bytes, Path, str],
    expected_sha256: str,
    chunk_size: int = DEFAULT_HASH_CHUNK_SIZE,
) -> bool:
    """Verifies that the SHA-256 checksum of source matches expected_sha256.

    Uses constant-time comparison (hmac.compare_digest) to prevent timing attack vulnerabilities.

    Args:
        source: Binary stream, bytes, or file path.
        expected_sha256: Expected 64-character hexadecimal SHA-256 string.
        chunk_size: Buffer chunk size in bytes.

    Returns:
        True if hashes match, False otherwise.
    """
    actual_hash = calculate_sha256(source, chunk_size=chunk_size)
    return hmac.compare_digest(
        actual_hash.lower(), expected_sha256.strip().lower()
    )


class HashingReader(io.RawIOBase):
    """Wraps a readable binary stream to calculate SHA-256 on-the-fly as chunks are read.

    Enables single-pass streaming uploads, storage writes, and checksum calculation
    without buffering entire files in memory.
    """

    def __init__(self, stream: BinaryIO) -> None:
        """Initializes the HashingReader wrapping the underlying binary stream.

        Args:
            stream: Source binary stream supporting read().
        """
        super().__init__()
        self._stream = stream
        self._hasher = hashlib.sha256()
        self._bytes_read = 0

    def readable(self) -> bool:
        """Indicates this stream is readable."""
        return True

    def read(self, size: int = -1) -> bytes:
        """Reads up to size bytes from the underlying stream and updates the hash digest.

        Args:
            size: Number of bytes to read (-1 for all).

        Returns:
            Bytes read from stream.
        """
        chunk = self._stream.read(size)
        if chunk:
            self._hasher.update(chunk)
            self._bytes_read += len(chunk)
        return chunk

    @property
    def hexdigest(self) -> str:
        """Returns the current 64-character lowercase hex digest of all bytes read so far."""
        return self._hasher.hexdigest()

    @property
    def bytes_read(self) -> int:
        """Returns total count of bytes processed through this reader."""
        return self._bytes_read
