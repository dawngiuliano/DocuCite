"""表格切分：一行数据对应一个可检索切片。"""

from ..schemas import Chunk, Document, Location, ParsedBlock, TableData


def chunk_table_blocks(document: Document, blocks: list[ParsedBlock]) -> list[Chunk]:
    """为每个表格数据行生成一个 Chunk，并在文字中重复表头。"""
    chunks: list[Chunk] = []
    for block in blocks:
        if block.kind != "table" or block.table is None:
            continue
        table = block.table
        for row_number, row in enumerate(table.rows, start=1):
            row_table = TableData(header=table.header, rows=[row])
            text = _row_to_text(table.header, row)
            location = _row_location(block.location, row_number)
            chunks.append(
                Chunk(
                    doc_id=document.doc_id,
                    filename=document.filename,
                    kind="table",
                    text=text,
                    table=row_table,
                    location=location,
                    source_block_ids=[block.block_id],
                )
            )
    return chunks


def _row_to_text(header: list[str] | None, row: list[str]) -> str:
    """把表头和一行数据转成适合 Embedding 的文字。"""
    row_text = " | ".join(row)
    if header is None:
        return f"数据：{row_text}"
    return f"表头：{' | '.join(header)}；数据：{row_text}"


def _row_location(location: Location, row_number: int) -> Location:
    """复制原位置并补充数据行范围。"""
    values = location.model_dump()
    values["table_index"] = location.table_index or 1
    values["row_start"] = row_number
    values["row_end"] = row_number
    return Location(**values)
