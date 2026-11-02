"""PDF Pre-Flight Inspection Service using PyMuPDF (fitz).

Provides structural and security inspection for incoming PDF files:
- Page count verification
- PDF specification version extraction
- Encryption and password-lock detection
- Corrupted stream and invalid object detection
- Metadata extraction (title, author, creator, creation/modification dates)
- Page geometry and dimension profiling (portrait/landscape)
"""

import io
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Union
import pymupdf
from pydantic import BaseModel, Field


class PdfInspectionError(Exception):
    """Base exception for PDF pre-flight inspection failures."""

    pass


class PdfCorruptedError(PdfInspectionError):
    """Raised when PDF binary is malformed, truncated, or unparseable."""

    pass


class PdfEncryptedError(PdfInspectionError):
    """Raised when PDF document is password-protected or encrypted."""

    pass


class PdfEmptyError(PdfInspectionError):
    """Raised when PDF document contains 0 pages or 0 bytes."""

    pass


class PdfPageGeometry(BaseModel):
    """Physical dimensions and orientation of a single PDF page."""

    page_number: int = Field(description="1-indexed page number")
    width: float = Field(description="Page width in points (1/72 inch)")
    height: float = Field(description="Page height in points (1/72 inch)")
    is_portrait: bool = Field(description="True if height >= width")


class PdfInspectionResult(BaseModel):
    """Comprehensive inspection report for a verified PDF document."""

    page_count: int = Field(description="Total number of rendered pages")
    file_size_bytes: int = Field(description="Binary size in bytes")
    pdf_version: str = Field(description="PDF specification standard version (e.g. '1.7')")
    is_encrypted: bool = Field(default=False, description="Whether document had encryption")
    title: Optional[str] = Field(default=None, description="Embedded document title")
    author: Optional[str] = Field(default=None, description="Embedded author name")
    creator: Optional[str] = Field(default=None, description="Application that created original content")
    producer: Optional[str] = Field(default=None, description="PDF producer software")
    creation_date: Optional[str] = Field(default=None, description="Original PDF creation timestamp")
    modification_date: Optional[str] = Field(default=None, description="Last modification timestamp")
    page_dimensions: List[PdfPageGeometry] = Field(
        default_factory=list, description="Per-page geometry list"
    )


class PDFInspector:
    """Stateless service performing pre-flight structural inspections on PDF binaries."""

    @classmethod
    def inspect(
        cls,
        source: Union[BinaryIO, bytes, str, Path],
    ) -> PdfInspectionResult:
        """Inspects a PDF stream, raw bytes, or filesystem path and extracts structural metadata.

        Args:
            source: Binary stream (supporting .read()), raw bytes, or filesystem path.

        Returns:
            PdfInspectionResult containing page count, version, metadata, and page geometry.

        Raises:
            PdfEmptyError: If source is 0 bytes or contains 0 pages.
            PdfEncryptedError: If document is password-locked or encrypted.
            PdfCorruptedError: If document structure is malformed or unreadable.
            FileNotFoundError: If a filesystem path is provided and does not exist.
            TypeError: If source type is unsupported.
        """
        raw_bytes: bytes

        if isinstance(source, bytes):
            raw_bytes = source
        elif isinstance(source, (str, Path)):
            file_path = Path(source)
            if not file_path.is_file():
                raise FileNotFoundError(f"PDF file not found: {file_path}")
            raw_bytes = file_path.read_bytes()
        elif hasattr(source, "read"):
            initial_pos = None
            if hasattr(source, "tell") and hasattr(source, "seek"):
                try:
                    initial_pos = source.tell()
                except (io.UnsupportedOperation, OSError):
                    initial_pos = None

            raw_bytes = source.read()

            if initial_pos is not None and hasattr(source, "seek"):
                source.seek(initial_pos)
        else:
            raise TypeError(f"Unsupported source type for PDF inspection: {type(source)}")

        if not raw_bytes:
            raise PdfEmptyError("Uploaded file is empty (0 bytes).")

        try:
            doc = pymupdf.open(stream=raw_bytes, filetype="pdf")
        except Exception as exc:
            raise PdfCorruptedError(f"Corrupted or invalid PDF binary: {str(exc)}") from exc

        try:
            if not doc.is_pdf:
                raise PdfCorruptedError("Supplied binary is not a valid PDF document.")

            # Scan for password locks and encryption
            if doc.is_encrypted or (hasattr(doc, "needs_pass") and doc.needs_pass):
                raise PdfEncryptedError(
                    "Password-protected or encrypted PDF documents are not supported for statutory CDSCO filings."
                )

            page_count = len(doc)
            if page_count == 0:
                raise PdfEmptyError("PDF document contains zero pages.")

            # Extract format / PDF specification version
            meta = doc.metadata or {}
            raw_format = meta.get("format") or ""
            if raw_format.startswith("PDF "):
                pdf_version = raw_format[4:].strip()
            elif raw_format.startswith("PDF-"):
                pdf_version = raw_format[4:].strip()
            else:
                pdf_version = raw_format or "1.4"

            # Extract geometry of each page
            page_geometries: List[PdfPageGeometry] = []
            try:
                for idx, page in enumerate(doc):
                    rect = page.rect
                    page_geometries.append(
                        PdfPageGeometry(
                            page_number=idx + 1,
                            width=round(rect.width, 2),
                            height=round(rect.height, 2),
                            is_portrait=rect.height >= rect.width,
                        )
                    )
            except Exception as exc:
                raise PdfCorruptedError(f"Error reading PDF page structure: {str(exc)}") from exc

            return PdfInspectionResult(
                page_count=page_count,
                file_size_bytes=len(raw_bytes),
                pdf_version=pdf_version,
                is_encrypted=False,
                title=meta.get("title") or None,
                author=meta.get("author") or None,
                creator=meta.get("creator") or None,
                producer=meta.get("producer") or None,
                creation_date=meta.get("creationDate") or None,
                modification_date=meta.get("modDate") or None,
                page_dimensions=page_geometries,
            )
        finally:
            doc.close()

