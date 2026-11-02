"""Unit tests for PDF Pre-Flight Inspection Service (PyMuPDF / fitz)."""

import io
from pathlib import Path
import pytest
import pymupdf

from app.services.pdf_inspector import (
    PDFInspector,
    PdfInspectionResult,
    PdfPageGeometry,
    PdfInspectionError,
    PdfCorruptedError,
    PdfEncryptedError,
    PdfEmptyError,
)


def create_sample_pdf(
    pages: int = 1,
    title: str = "",
    author: str = "",
    width: float = 595.0,
    height: float = 842.0,
    encrypt: bool = False,
    password: str = "secure123",
) -> bytes:
    """Helper creating memory-buffered PDF binaries with configurable attributes."""
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page(width=width, height=height)

    if title or author:
        doc.set_metadata({
            "title": title,
            "author": author,
            "creator": "CDSCO Test Suite",
            "producer": "PyMuPDF Test Engine",
        })

    if encrypt:
        return doc.tobytes(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw=password,
            user_pw=password,
        )

    return doc.tobytes()


def test_inspect_valid_single_page_pdf():
    """Verifies standard 1-page PDF structural and geometry extraction."""
    pdf_bytes = create_sample_pdf(pages=1, width=595.0, height=842.0)
    result = PDFInspector.inspect(pdf_bytes)

    assert isinstance(result, PdfInspectionResult)
    assert result.page_count == 1
    assert result.file_size_bytes == len(pdf_bytes)
    assert result.is_encrypted is False
    assert result.pdf_version in ("1.7", "1.4", "1.5", "1.6")
    assert len(result.page_dimensions) == 1

    page = result.page_dimensions[0]
    assert page.page_number == 1
    assert page.width == 595.0
    assert page.height == 842.0
    assert page.is_portrait is True


def test_inspect_multi_page_pdf_tc_ur02_01():
    """Verifies TC-UR02-01: multi-page PDF inspection correctly records page_count: 3."""
    pdf_bytes = create_sample_pdf(pages=3)
    result = PDFInspector.inspect(pdf_bytes)

    assert result.page_count == 3
    assert len(result.page_dimensions) == 3
    for idx, page in enumerate(result.page_dimensions):
        assert page.page_number == idx + 1
        assert page.is_portrait is True


def test_inspect_landscape_orientation():
    """Verifies detection of landscape page orientation when width > height."""
    # A4 landscape: width 842, height 595
    pdf_bytes = create_sample_pdf(pages=1, width=842.0, height=595.0)
    result = PDFInspector.inspect(pdf_bytes)

    assert result.page_count == 1
    assert result.page_dimensions[0].width == 842.0
    assert result.page_dimensions[0].height == 595.0
    assert result.page_dimensions[0].is_portrait is False


def test_inspect_metadata_extraction():
    """Verifies extraction of embedded document title, author, and producer strings."""
    pdf_bytes = create_sample_pdf(
        pages=1,
        title="ISO 13485:2016 Audit Report",
        author="Quality Certification Bureau",
    )
    result = PDFInspector.inspect(pdf_bytes)

    assert result.title == "ISO 13485:2016 Audit Report"
    assert result.author == "Quality Certification Bureau"
    assert result.creator == "CDSCO Test Suite"
    assert result.producer == "PyMuPDF Test Engine"


def test_inspect_encrypted_pdf_rejection():
    """Verifies that password-locked or encrypted PDFs raise PdfEncryptedError."""
    encrypted_bytes = create_sample_pdf(pages=1, encrypt=True, password="cdsco_pass")

    with pytest.raises(PdfEncryptedError, match="Password-protected or encrypted PDF documents are not supported"):
        PDFInspector.inspect(encrypted_bytes)


def test_inspect_corrupted_pdf_rejection():
    """Verifies that truncated or malformed PDF binaries raise PdfCorruptedError."""
    corrupted_bytes = b"%PDF-1.4\x00\xff\xfe\xca\xfe\xba\xbe random corrupt unparseable data"

    with pytest.raises(PdfCorruptedError):
        PDFInspector.inspect(corrupted_bytes)


def test_inspect_empty_bytes_rejection():
    """Verifies that empty binaries raise PdfEmptyError."""
    with pytest.raises(PdfEmptyError, match="empty \\(0 bytes\\)"):
        PDFInspector.inspect(b"")


def test_inspect_zero_page_pdf_rejection():
    """Verifies that valid PDF headers with zero rendered pages raise PdfEmptyError."""
    zero_page_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"

    with pytest.raises(PdfEmptyError, match="contains zero pages"):
        PDFInspector.inspect(zero_page_bytes)


def test_inspect_seekable_stream_and_rewind():
    """Verifies that inspecting a stream rewinds its file pointer to original offset."""
    pdf_bytes = create_sample_pdf(pages=2)
    stream = io.BytesIO(pdf_bytes)

    # Move to initial offset 0
    stream.seek(0)
    result = PDFInspector.inspect(stream)

    assert result.page_count == 2
    # Verify stream pointer rewound to 0
    assert stream.tell() == 0
    # Stream can still be read
    assert stream.read() == pdf_bytes


def test_inspect_from_file_path(tmp_path: Path):
    """Verifies inspection of PDF binaries directly from filesystem paths."""
    pdf_bytes = create_sample_pdf(pages=1, title="Path Test")
    test_file = tmp_path / "sample.pdf"
    test_file.write_bytes(pdf_bytes)

    result = PDFInspector.inspect(test_file)
    assert result.page_count == 1
    assert result.title == "Path Test"
    assert result.file_size_bytes == len(pdf_bytes)


def test_inspect_missing_file_path_raises_filenotfound():
    """Verifies that non-existent filesystem paths raise FileNotFoundError."""
    missing_path = Path("non_existent_cdsco_file_12345.pdf")
    with pytest.raises(FileNotFoundError):
        PDFInspector.inspect(missing_path)


def test_inspect_unsupported_source_type():
    """Verifies that invalid source types raise TypeError."""
    with pytest.raises(TypeError, match="Unsupported source type"):
        PDFInspector.inspect(12345)  # type: ignore
