"""Unit tests for DocumentConverter service."""

import io
from pathlib import Path
import pytest
from PIL import Image
import docx
import pymupdf

from app.services.document_converter import (
    DocumentConverter,
    DocumentConversionError,
    UnsupportedFormatError,
)


def test_supported_extensions():
    """Verifies that all required statutory and office formats are recognized."""
    exts = DocumentConverter.get_supported_extensions()
    assert ".pdf" in exts
    assert ".docx" in exts
    assert ".jpg" in exts
    assert ".jpeg" in exts
    assert ".png" in exts
    assert ".webp" in exts
    assert ".tiff" in exts
    assert ".tif" in exts
    assert ".bmp" in exts

    assert DocumentConverter.is_supported("document.pdf") is True
    assert DocumentConverter.is_supported("photo.jpg") is True
    assert DocumentConverter.is_supported("scan.PNG") is True
    assert DocumentConverter.is_supported("draft.docx") is True
    assert DocumentConverter.is_supported("archive.zip") is False
    assert DocumentConverter.is_supported("script.py") is False


def test_unsupported_format_raises():
    """Verifies that unsupported file extensions raise UnsupportedFormatError."""
    stream = io.BytesIO(b"binary content")
    with pytest.raises(UnsupportedFormatError) as exc_info:
        DocumentConverter.convert_to_pdf(stream, "trojan.exe")
    assert "Unsupported file format '.exe'" in str(exc_info.value)


def test_pdf_passthrough():
    """Verifies that standard PDF binaries pass through unchanged without re-encoding."""
    pdf_doc = pymupdf.open()
    pdf_doc.new_page(width=595.0, height=842.0)
    pdf_bytes = pdf_doc.tobytes()

    stream = io.BytesIO(pdf_bytes)
    result = DocumentConverter.convert_to_pdf(stream, "statutory_cert.pdf")

    assert result.converted is False
    assert result.source_format == "pdf"
    assert result.file_size_bytes == len(pdf_bytes)

    # Verify stream is valid PDF
    header = result.pdf_stream.read(4)
    assert header == b"%PDF"


def test_invalid_pdf_header_raises():
    """Verifies that a file named .pdf without %PDF magic bytes raises DocumentConversionError."""
    fake_stream = io.BytesIO(b"NOT_A_VALID_PDF_HEADER")
    with pytest.raises(DocumentConversionError) as exc_info:
        DocumentConverter.convert_to_pdf(fake_stream, "spoofed.pdf")
    assert "File does not start with standard PDF header (%PDF)" in str(exc_info.value)


def test_convert_jpeg_to_pdf():
    """Verifies that JPEG images are cleanly converted into valid PDF streams."""
    img = Image.new("RGB", (400, 300), color=(50, 100, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    result = DocumentConverter.convert_to_pdf(buf, "lab_photo.jpg")

    assert result.converted is True
    assert result.source_format == "jpg"
    assert result.file_size_bytes > 0

    # Inspect resulting PDF
    pdf = pymupdf.open("pdf", result.pdf_stream.read())
    assert pdf.page_count == 1
    assert pdf[0].rect.width > 0
    assert pdf[0].rect.height > 0


def test_convert_png_rgba_to_pdf():
    """Verifies that transparent PNGs blend cleanly on white backgrounds without error."""
    img = Image.new("RGBA", (200, 200), color=(255, 0, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    result = DocumentConverter.convert_to_pdf(buf, "stamp.png")

    assert result.converted is True
    assert result.source_format == "png"

    pdf = pymupdf.open("pdf", result.pdf_stream.read())
    assert pdf.page_count == 1


def test_convert_webp_to_pdf():
    """Verifies that WebP images convert to valid PDFs."""
    img = Image.new("RGB", (250, 250), color=(30, 180, 70))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    buf.seek(0)

    result = DocumentConverter.convert_to_pdf(buf, "graphic.webp")

    assert result.converted is True
    assert result.source_format == "webp"

    pdf = pymupdf.open("pdf", result.pdf_stream.read())
    assert pdf.page_count == 1


def test_convert_bmp_to_pdf():
    """Verifies that BMP images convert to valid PDFs."""
    img = Image.new("RGB", (100, 100), color=(200, 200, 50))
    buf = io.BytesIO()
    img.save(buf, format="BMP")
    buf.seek(0)

    result = DocumentConverter.convert_to_pdf(buf, "legacy_scan.bmp")

    assert result.converted is True
    assert result.source_format == "bmp"

    pdf = pymupdf.open("pdf", result.pdf_stream.read())
    assert pdf.page_count == 1


def test_corrupted_image_raises():
    """Verifies that corrupted image bytes raise DocumentConversionError."""
    buf = io.BytesIO(b"NOT_AN_IMAGE_RANDOM_GARBAGE_BYTES")
    with pytest.raises(DocumentConversionError) as exc_info:
        DocumentConverter.convert_to_pdf(buf, "broken.jpg")
    assert "Unidentified or invalid image binary" in str(exc_info.value)


def test_convert_docx_to_pdf():
    """Verifies that Microsoft Word .docx files convert to styled A4 PDF documents."""
    doc = docx.Document()
    doc.add_heading("Power of Attorney (Statutory Form)", level=0)
    doc.add_paragraph("This instrument authorizes the regulatory agent to act on behalf of the manufacturer.")
    doc.add_heading("Section 1: Scope", level=1)
    doc.add_paragraph("Medical device class C and D registrations.")

    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Field"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Agent Name"
    table.cell(1, 1).text = "MedTech Regulatory Consultants India LLP"

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    result = DocumentConverter.convert_to_pdf(buf, "poa_draft.docx")

    assert result.converted is True
    assert result.source_format == "docx"
    assert result.file_size_bytes > 0

    pdf = pymupdf.open("pdf", result.pdf_stream.read())
    assert pdf.page_count >= 1

    extracted_text = pdf[0].get_text()
    assert "Power of Attorney (Statutory Form)" in extracted_text
    assert "Scope" in extracted_text
    assert "MedTech Regulatory Consultants India LLP" in extracted_text


def test_corrupted_docx_raises():
    """Verifies that corrupted docx bytes raise DocumentConversionError."""
    buf = io.BytesIO(b"NOT_A_VALID_DOCX_OR_ZIP_FILE")
    with pytest.raises(DocumentConversionError) as exc_info:
        DocumentConverter.convert_to_pdf(buf, "broken.docx")
    assert "Failed to convert Word document (.docx) to PDF" in str(exc_info.value)
