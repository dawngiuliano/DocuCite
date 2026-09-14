"""文本块切分。

这里不做向量化，只把较长的原文整理成适合后续 Embedding 的小片段。
"""

from ..schemas import Chunk, Document, ParsedBlock


def chunk_text_blocks(
    document: Document,
    blocks: list[ParsedBlock],
    max_chars: int = 1000,
    overlap: int = 100,
) -> list[Chunk]:
    """把文本块合并并按字符数切分。

    相邻的短文本会尽量合并；一个文本块超过 ``max_chars`` 时，会按
    ``overlap`` 保留少量重复内容，避免上下文刚好在边界处被截断。
    """
    chunks: list[Chunk] = []
    pending_texts: list[str] = []
    pending_ids: list[str] = []
    pending_location = None

    def flush_pending() -> None:
        """把目前积累的短文本生成一个切片。"""
        nonlocal pending_location
        if not pending_texts:
            return
        chunks.append(
            Chunk(
                doc_id=document.doc_id,
                filename=document.filename,
                kind="text",
                text="\n\n".join(pending_texts),
                location=pending_location,
                source_block_ids=pending_ids.copy(),
            )
        )
        pending_texts.clear()
        pending_ids.clear()
        pending_location = None

    for block in blocks:
        if block.kind != "text":
            continue
        text = block.text.strip()
        if not text:
            continue

        # 一个 ParsedBlock 可能来自 PDF 的整页文本，因此还要按段落拆一次。
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        if not paragraphs:
            paragraphs = [text]

        for paragraph in paragraphs:
            if len(paragraph) > max_chars:
                flush_pending()
                chunks.extend(_split_long_text(document, block, paragraph, max_chars, overlap))
                continue

            candidate = "\n\n".join(pending_texts + [paragraph])
            if pending_texts and len(candidate) > max_chars:
                flush_pending()
            if not pending_texts:
                pending_location = block.location
            pending_texts.append(paragraph)
            # 一个 ParsedBlock 可能拆成多个段落，但来源 ID 在一个 Chunk 中只记录一次。
            if block.block_id not in pending_ids:
                pending_ids.append(block.block_id)

    flush_pending()
    return chunks


def _split_long_text(
    document: Document,
    block: ParsedBlock,
    text: str,
    max_chars: int,
    overlap: int,
) -> list[Chunk]:
    """切分一个超过上限的文本块，并保留相邻切片的重叠字符。"""
    chunks: list[Chunk] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(
                Chunk(
                    doc_id=document.doc_id,
                    filename=document.filename,
                    kind="text",
                    text=piece,
                    location=block.location,
                    source_block_ids=[block.block_id],
                )
            )
        if end == len(text):
            break
        start = end - overlap
    return chunks
