"""切块统一入口。"""

from ..schemas import Chunk, Document, ParsedBlock
from .table import chunk_table_blocks
from .text import chunk_text_blocks


def chunk_blocks(
    document: Document,
    blocks: list[ParsedBlock],
    max_chars: int = 1000,
    overlap: int = 100,
) -> list[Chunk]:
    """将解析块转换为文本切片和表格切片。"""
    if max_chars <= 0:
        raise ValueError("max_chars 必须大于 0")
    if overlap < 0 or overlap >= max_chars:
        raise ValueError("overlap 必须大于等于 0 且小于 max_chars")
    for block in blocks:
        if block.doc_id != document.doc_id:
            raise ValueError(f"解析块 {block.block_id} 不属于文档 {document.doc_id}")

    # 分开处理后再合并，确保表格不会被当成普通文字切碎。
    text_chunks = chunk_text_blocks(document, blocks, max_chars, overlap)
    table_chunks = chunk_table_blocks(document, blocks)
    return text_chunks + table_chunks
