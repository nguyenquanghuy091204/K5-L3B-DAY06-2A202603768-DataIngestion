"""Read and normalize source data. TODO: implement functions."""
from pathlib import Path
from .models import DocumentPage


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """TODO: extract each physical page; keep its page number and source.
    Detect and record pages with no text. OCR, when needed, is a separate step.
    """
    from pypdf import PdfReader
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    chapter_ranges = [
        (4, 7, "Laying Plans"),
        (8, 10, "Waging War"),
        (11, 14, "Attack by Stratagem"),
        (15, 17, "Tactical Dispositions"),
        (18, 21, "Energy"),
        (22, 27, "Weak Points and Strong"),
        (28, 32, "Maneuvering"),
        (33, 35, "Variation in Tactics"),
        (36, 42, "The Army on the March"),
        (43, 48, "Terrain"),
        (49, 58, "The Nine Situations"),
        (59, 61, "The Attack by Fire"),
        (62, 65, "The Use of Spies"),
    ]
    reader = PdfReader(str(path))
    pages: list[DocumentPage] = []
    for page_num, pdf_page in enumerate(reader.pages, start=1):
        raw_text = pdf_page.extract_text() or ""
        cleaned = normalize_text(raw_text)
        section = "front_or_back_matter"
        is_content_page = False
        for start_p, end_p, chap_name in chapter_ranges:
            if start_p <= page_num <= end_p:
                section = chap_name
                is_content_page = True
                break
        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=page_num,
                text=cleaned,
                metadata={
                    "section": section,
                    "is_content_page": is_content_page and len(cleaned) > 50,
                    "is_empty": len(cleaned) == 0,
                    "char_count": len(cleaned),
                },
            )
        )
    return pages


def normalize_text(text: str) -> str:
    """TODO: normalize Unicode and whitespace without discarding useful structure."""
    import re
    import unicodedata
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\ufffd", "")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()