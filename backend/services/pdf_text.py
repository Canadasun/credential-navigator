"""Text from an uploaded PDF. Scanned (image-only) PDFs are reported, not guessed at."""
from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PAGES = 60
MIN_CHARS_PER_PAGE = 40  # below this on average, the PDF is almost certainly scanned images


class UnreadableDocument(ValueError):
    """The upload can't be turned into text without OCR, or isn't a usable PDF."""


def extract_text(data: bytes) -> str:
    if not data.startswith(b"%PDF-"):
        raise UnreadableDocument("The file is not a PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise UnreadableDocument("The PDF is password-protected.")
        if len(reader.pages) > MAX_PAGES:
            raise UnreadableDocument(f"The PDF has more than {MAX_PAGES} pages.")
        pages = [page.extract_text() or "" for page in reader.pages]
    except PdfReadError as error:
        raise UnreadableDocument("The PDF could not be read.") from error
    text = "\n".join(pages)
    if len(text.strip()) < MIN_CHARS_PER_PAGE * max(len(pages), 1):
        raise UnreadableDocument("The PDF looks scanned (no text layer). Scanned documents need OCR, "
                                 "which is not available yet.")
    return text
