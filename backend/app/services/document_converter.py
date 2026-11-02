"""Stateless document format conversion service.

Converts non-PDF evidence files (images, Word .docx) into standardized
PDF documents on ingestion so that subsequent operations (inspection,
watermarking, bookmarking, dossier assembly) operate on a uniform PDF pipeline.
"""

from dataclasses import dataclass
import io
from pathlib import Path
from typing import Any, BinaryIO, Set
import pymupdf
from PIL import Image, UnidentifiedImageError
import mammoth


class DocumentConversionError(Exception):
    """Raised when a document cannot be parsed or converted into PDF."""

    pass


class UnsupportedFormatError(DocumentConversionError):
    """Raised when an uploaded file format is not permitted."""

    pass


@dataclass
class ConvertedDocument:
    """Result of converting or validating an incoming evidence binary."""

    pdf_stream: Any
    file_size_bytes: int
    converted: bool
    source_format: str


class DocumentConverter:
    """Stateless conversion engine transforming images and Word docs into standardized PDFs."""

    SUPPORTED_PDF_EXTENSIONS: Set[str] = {".pdf"}
    SUPPORTED_IMAGE_EXTENSIONS: Set[str] = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".tiff",
        ".tif",
        ".bmp",
    }
    SUPPORTED_DOCX_EXTENSIONS: Set[str] = {".docx"}
    ALL_SUPPORTED_EXTENSIONS: Set[str] = (
        SUPPORTED_PDF_EXTENSIONS
        | SUPPORTED_IMAGE_EXTENSIONS
        | SUPPORTED_DOCX_EXTENSIONS
    )

    @classmethod
    def get_supported_extensions(cls) -> Set[str]:
        """Returns the set of all supported file extensions (lowercased, with leading dot)."""
        return set(cls.ALL_SUPPORTED_EXTENSIONS)

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Returns True if the filename has a supported extension."""
        ext = Path(filename).suffix.lower()
        return ext in cls.ALL_SUPPORTED_EXTENSIONS

    @classmethod
    def convert_to_pdf(
        cls,
        stream: BinaryIO,
        filename: str,
    ) -> ConvertedDocument:
        """Inspects the input stream and filename, converts non-PDF formats to PDF,

        and returns a ConvertedDocument with a seek(0) stream ready for storage/inspection.
        """
        ext = Path(filename).suffix.lower()
        if not ext or ext not in cls.ALL_SUPPORTED_EXTENSIONS:
            allowed = ", ".join(sorted(cls.ALL_SUPPORTED_EXTENSIONS))
            raise UnsupportedFormatError(
                f"Unsupported file format '{ext or 'unknown'}'. Permitted formats: {allowed}."
            )

        stream.seek(0)

        # 1. Native PDF handling
        if ext in cls.SUPPORTED_PDF_EXTENSIONS:
            header = stream.read(4)
            stream.seek(0)
            if header != b"%PDF":
                raise DocumentConversionError(
                    "Invalid file format. File does not start with standard PDF header (%PDF)."
                )
            stream.seek(0, io.SEEK_END)
            size = stream.tell()
            stream.seek(0)
            return ConvertedDocument(
                pdf_stream=stream,
                file_size_bytes=size,
                converted=False,
                source_format="pdf",
            )

        # 2. Image to PDF conversion (JPG, PNG, WebP, TIFF, BMP)
        if ext in cls.SUPPORTED_IMAGE_EXTENSIONS:
            return cls._convert_image_to_pdf(stream, ext)

        # 3. Word DOCX to PDF conversion
        if ext in cls.SUPPORTED_DOCX_EXTENSIONS:
            return cls._convert_docx_to_pdf(stream)

        raise UnsupportedFormatError(f"Unsupported format '{ext}'.")

    @classmethod
    def _convert_image_to_pdf(cls, stream: BinaryIO, ext: str) -> ConvertedDocument:
        """Converts single or multi-frame image into a standardized PDF."""
        try:
            pil_img = Image.open(stream)
            frames = []
            num_frames = getattr(pil_img, "n_frames", 1)

            for frame_idx in range(num_frames):
                pil_img.seek(frame_idx)
                frame = pil_img.copy()

                # Flatten transparency on white background to prevent dark artifacts
                if frame.mode in ("RGBA", "LA", "P"):
                    bg = Image.new("RGB", frame.size, (255, 255, 255))
                    if frame.mode == "P":
                        frame = frame.convert("RGBA")
                    mask = frame.split()[-1] if frame.mode == "RGBA" else None
                    bg.paste(frame, mask=mask)
                    frame = bg
                elif frame.mode != "RGB":
                    frame = frame.convert("RGB")

                frames.append(frame)

            if not frames:
                raise DocumentConversionError("Image file contains no readable frames.")

            pdf_buffer = io.BytesIO()
            if len(frames) == 1:
                frames[0].save(pdf_buffer, format="PDF", resolution=150.0)
            else:
                frames[0].save(
                    pdf_buffer,
                    format="PDF",
                    save_all=True,
                    append_images=frames[1:],
                    resolution=150.0,
                )

            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.seek(0)
            return ConvertedDocument(
                pdf_stream=pdf_buffer,
                file_size_bytes=len(pdf_bytes),
                converted=True,
                source_format=ext.lstrip("."),
            )
        except UnidentifiedImageError as exc:
            raise DocumentConversionError(f"Unidentified or invalid image binary: {str(exc)}") from exc
        except Exception as exc:
            raise DocumentConversionError(f"Failed to convert image to PDF: {str(exc)}") from exc

    @classmethod
    def _convert_docx_to_pdf(cls, stream: BinaryIO) -> ConvertedDocument:
        """Converts Microsoft Word DOCX to HTML via mammoth and renders to PDF via PyMuPDF Story."""
        try:
            conversion_res = mammoth.convert_to_html(stream)
            raw_html = conversion_res.value

            # Wrap in clean, print-friendly styling suitable for A4 CDSCO dossiers
            styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 20mm;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a202c;
  }}
  h1 {{ font-size: 18pt; font-weight: 700; margin-top: 0; margin-bottom: 14pt; border-bottom: 1px solid #e2e8f0; padding-bottom: 6pt; }}
  h2 {{ font-size: 14pt; font-weight: 600; margin-top: 14pt; margin-bottom: 8pt; }}
  h3 {{ font-size: 12pt; font-weight: 600; margin-top: 10pt; margin-bottom: 6pt; }}
  p {{ margin-top: 0; margin-bottom: 8pt; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 10pt;
    margin-bottom: 12pt;
    font-size: 10pt;
  }}
  th, td {{
    border: 1px solid #cbd5e0;
    padding: 6pt 8pt;
    text-align: left;
    vertical-align: top;
  }}
  th {{
    background-color: #f7fafc;
    font-weight: 600;
  }}
  ul, ol {{ margin-top: 0; margin-bottom: 8pt; padding-left: 20pt; }}
  li {{ margin-bottom: 4pt; }}
</style>
</head>
<body>
{raw_html}
</body>
</html>"""

            story = pymupdf.Story(html=styled_html)
            pdf_buffer = io.BytesIO()
            writer = pymupdf.DocumentWriter(pdf_buffer)

            # Standard A4: 595.3 x 841.9 pt, with 40 pt margins
            rect = pymupdf.Rect(40, 40, 595.3 - 40, 841.9 - 40)
            mediabox = pymupdf.Rect(0, 0, 595.3, 841.9)

            more = 1
            while more:
                dev = writer.begin_page(mediabox)
                more, _ = story.place(rect)
                story.draw(dev)
                writer.end_page()
            writer.close()

            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.seek(0)

            return ConvertedDocument(
                pdf_stream=pdf_buffer,
                file_size_bytes=len(pdf_bytes),
                converted=True,
                source_format="docx",
            )
        except Exception as exc:
            raise DocumentConversionError(
                f"Failed to convert Word document (.docx) to PDF: {str(exc)}"
            ) from exc
