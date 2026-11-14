"""Implement fixed-size and structure-aware chunking."""
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    """TODO: split text into overlapping windows and retain page metadata."""
    import re
    clean_text = re.sub(r"\s+", " ", page.text).strip()
    if not clean_text:
        return []
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and < size")
    chunks: list[Chunk] = []
    step = size - overlap
    idx = 0
    for start in range(0, len(clean_text), step):
        end = min(start + size, len(clean_text))
        window = clean_text[start:end].strip()
        if window:
            chunks.append(
                Chunk(
                    chunk_id=f"{page.document_id}_p{page.page:03d}_fixed_{idx:03d}",
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=window,
                    metadata=dict(page.metadata),
                )
            )
            idx += 1
        if end >= len(clean_text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int) -> list[Chunk]:
    """TODO: group paragraphs, split oversized paragraphs and retain metadata."""
    import re
    clean_text = re.sub(r"\s+", " ", page.text).strip()
    if not clean_text:
        return []
    if max_size <= 0:
        raise ValueError("max_size must be positive")
    # Tách theo các điều khoản đánh số (1., 2., ...) hoặc câu văn hoàn chỉnh
    segments = re.split(r"(?<=[.!?])\s+(?=\d+[,0-9]*\.\s+|\([0-9]+\)\s+)", clean_text)
    chunks: list[Chunk] = []
    current = ""
    idx = 0
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        if len(seg) > max_size:
            if current:
                chunks.append(
                    Chunk(
                        chunk_id=f"{page.document_id}_p{page.page:03d}_para_{idx:03d}",
                        document_id=page.document_id,
                        source=page.source,
                        page=page.page,
                        text=current,
                        metadata=dict(page.metadata),
                    )
                )
                idx += 1
                current = ""
            for i in range(0, len(seg), max_size):
                part = seg[i : i + max_size].strip()
                if part:
                    chunks.append(
                        Chunk(
                            chunk_id=f"{page.document_id}_p{page.page:03d}_para_{idx:03d}",
                            document_id=page.document_id,
                            source=page.source,
                            page=page.page,
                            text=part,
                            metadata=dict(page.metadata),
                        )
                    )
                    idx += 1
        elif len(current) + len(seg) + 1 <= max_size:
            current = f"{current} {seg}".strip()
        else:
            if current:
                chunks.append(
                    Chunk(
                        chunk_id=f"{page.document_id}_p{page.page:03d}_para_{idx:03d}",
                        document_id=page.document_id,
                        source=page.source,
                        page=page.page,
                        text=current,
                        metadata=dict(page.metadata),
                    )
                )
                idx += 1
            current = seg
    if current:
        chunks.append(
            Chunk(
                chunk_id=f"{page.document_id}_p{page.page:03d}_para_{idx:03d}",
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=current,
                metadata=dict(page.metadata),
            )
        )
    return chunks
