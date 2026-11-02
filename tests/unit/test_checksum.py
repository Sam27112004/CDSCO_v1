import hashlib
import io
import pytest

from app.services.storage.checksum import (
    ChecksumError,
    ChecksumMismatchError,
    HashingReader,
    calculate_sha256,
    verify_sha256,
)


def test_calculate_sha256_bytes():
    """Verifies SHA-256 calculation on raw bytes."""
    # Known SHA-256 for empty bytes
    empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert calculate_sha256(b"") == empty_hash

    # Test payload
    payload = b"CDSCO Statutory Evidence Document 2026"
    expected = hashlib.sha256(payload).hexdigest()
    assert calculate_sha256(payload) == expected


def test_calculate_sha256_stream_and_rewind():
    """Verifies SHA-256 on a seekable binary stream and verifies stream is rewound."""
    payload = b"%PDF-1.7 ISO 13485 Audit Certificate Payload Data"
    expected = hashlib.sha256(payload).hexdigest()

    stream = io.BytesIO(payload)
    # Stream is at position 0
    calculated = calculate_sha256(stream)
    assert calculated == expected

    # Stream should be rewound to position 0 so next reader doesn't get EOF
    assert stream.tell() == 0
    assert stream.read() == payload


def test_calculate_sha256_stream_initial_offset():
    """Verifies seekable stream starting at offset > 0 is rewound to that exact offset."""
    payload = b"HEADER_PREFIX" + b"REAL_CONTENT_BYTES"
    stream = io.BytesIO(payload)
    stream.seek(13)  # Offset after header prefix

    expected = hashlib.sha256(b"REAL_CONTENT_BYTES").hexdigest()
    calculated = calculate_sha256(stream)
    assert calculated == expected
    assert stream.tell() == 13


def test_calculate_sha256_file_path(tmp_path):
    """Verifies SHA-256 calculation on physical files by Path and str."""
    test_file = tmp_path / "iso_certificate.pdf"
    content = b"%PDF-1.4 Clinical Investigation Report Data" * 500
    test_file.write_bytes(content)
    expected = hashlib.sha256(content).hexdigest()

    # Via Path object
    assert calculate_sha256(test_file) == expected
    # Via string path
    assert calculate_sha256(str(test_file)) == expected

    # Non-existent file raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="File not found for checksum"):
        calculate_sha256(tmp_path / "non_existent.pdf")


def test_calculate_sha256_chunking():
    """Verifies chunked hashing produces identical digest to single-pass."""
    large_payload = b"A" * 150000  # 150 KB (> default 64KB chunk)
    expected = hashlib.sha256(large_payload).hexdigest()

    # Small chunk size forces multiple loop iterations
    calculated = calculate_sha256(io.BytesIO(large_payload), chunk_size=1024)
    assert calculated == expected


def test_calculate_sha256_unsupported_type():
    """Verifies TypeError raised on invalid input types."""
    with pytest.raises(TypeError, match="Unsupported source type"):
        calculate_sha256(12345)

    with pytest.raises(TypeError, match="Unsupported source type"):
        calculate_sha256({"data": "invalid"})


def test_verify_sha256_matching_and_case_insensitive():
    """Verifies verify_sha256 returns True and handles whitespace/casing."""
    payload = b"Free Sale Certificate - Device Model X"
    expected = hashlib.sha256(payload).hexdigest()

    # Exact match
    assert verify_sha256(payload, expected) is True

    # Uppercase expected hash
    assert verify_sha256(payload, expected.upper()) is True

    # Expected hash with leading/trailing whitespace
    assert verify_sha256(payload, f"  {expected}  ") is True


def test_verify_sha256_mismatched():
    """Verifies verify_sha256 returns False when content or hash is altered."""
    payload = b"Original Authentic Content"
    expected = hashlib.sha256(payload).hexdigest()

    # Tampered content
    tampered = b"Tampered Modified Content"
    assert verify_sha256(tampered, expected) is False

    # Fake hash
    assert (
        verify_sha256(
            payload,
            "0000000000000000000000000000000000000000000000000000000000000000",
        )
        is False
    )


def test_hashing_reader_streaming():
    """Verifies HashingReader calculates SHA-256 on the fly while streaming."""
    raw_data = b"STREAMING_PAYLOAD_CHUNK_1" + b"STREAMING_PAYLOAD_CHUNK_2" * 100
    expected_hash = hashlib.sha256(raw_data).hexdigest()

    reader = HashingReader(io.BytesIO(raw_data))
    assert reader.readable() is True
    assert reader.bytes_read == 0

    # Read in chunks of 50 bytes
    accumulated = bytearray()
    while True:
        chunk = reader.read(50)
        if not chunk:
            break
        accumulated.extend(chunk)

    assert bytes(accumulated) == raw_data
    assert reader.bytes_read == len(raw_data)
    assert reader.hexdigest == expected_hash


def test_checksum_exception_hierarchy():
    """Verifies inheritance tree of checksum exceptions."""
    assert issubclass(ChecksumError, Exception)
    assert issubclass(ChecksumMismatchError, ChecksumError)
