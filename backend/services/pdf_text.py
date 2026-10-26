"""Text from an uploaded PDF: the text layer when there is one, otherwise local OCR.

OCR uses Tesseract on this machine (see Dockerfile), so scanned documents are not sent
to any outside service. Without Tesseract installed, scanned PDFs are refused with a
clear message instead of being guessed at.
"""
from __future__ import annotations

import io
import shutil
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PAGES = 60
MAX_OCR_PAGES = 20         # OCR takes a few seconds per page
OCR_DPI = 300
OCR_LANGUAGES = "eng+fra"  # Canada's official languages; add others as packs are installed
MIN_CHARS_PER_PAGE = 40    # below this on average, the PDF is almost certainly scanned images
LOW_CONFIDENCE = 70        # Tesseract's mean word confidence (0-100)


class UnreadableDocument(ValueError):
    """The upload can't be turned into text, or isn't a usable PDF."""


@dataclass
class ExtractedText:
    text: str
    method: str                       # "text_layer" or "ocr"
    pages: int
    ocr_confidence: float | None = None


def ocr_available() -> bool:
    return shutil.which("tesseract") is not None


def extract_text(data: bytes) -> ExtractedText:
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
    if len(text.strip()) >= MIN_CHARS_PER_PAGE * max(len(pages), 1):
        return ExtractedText(text, "text_layer", len(pages))
    if not ocr_available():
        raise UnreadableDocument("The PDF looks scanned (no text layer), and OCR is not installed here. "
                                 "Run the API in its Docker image, which includes OCR.")
    if len(pages) > MAX_OCR_PAGES:
        raise UnreadableDocument(f"Scanned PDFs are limited to {MAX_OCR_PAGES} pages.")
    return ocr(data)


def ocr(data: bytes) -> ExtractedText:
    import pypdfium2
    import pytesseract

    document = pypdfium2.PdfDocument(data)
    texts, confidences = [], []
    try:
        for page in document:
            image = page.render(scale=OCR_DPI / 72).to_pil().convert("L")
            # --psm 6: a single uniform block of text, which keeps transcript rows on one line.
            words = pytesseract.image_to_data(image, lang=OCR_LANGUAGES, config="--psm 6",
                                              output_type=pytesseract.Output.DICT)
            confidences += [float(c) for c, w in zip(words["conf"], words["text"]) if w.strip() and float(c) >= 0]
            texts.append(_lines(words))
    finally:
        document.close()
    text = "\n".join(texts)
    if len(text.strip()) < MIN_CHARS_PER_PAGE:
        raise UnreadableDocument("No readable text was found, even with OCR. Try a clearer scan (300 dpi).")
    confidence = round(sum(confidences) / len(confidences), 1) if confidences else None
    return ExtractedText(text, "ocr", len(texts), confidence)


def _lines(words: dict) -> str:
    """Rebuild lines from Tesseract's word boxes (block, paragraph, line numbers)."""
    lines: dict[tuple, list[str]] = {}
    for i, word in enumerate(words["text"]):
        if word.strip():
            key = (words["block_num"][i], words["par_num"][i], words["line_num"][i])
            lines.setdefault(key, []).append(word)
    return "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
