"""项目中各模块共同使用的数据结构。

解析器产生 ParsedBlock，切块器产生 Chunk，Location 负责保存引用位置。
所有位置编号从 1 开始；无法知道页码时使用 None，不能猜一个页码。
"""

from typing import Annotated, Literal, Self
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator


NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Position = Annotated[int, Field(strict=True, ge=1)]


class Schema(BaseModel):
    """所有模型的父类：禁止传入没有声明的字段。"""
    model_config = ConfigDict(extra="forbid")


class Location(Schema):
    """原文位置；无法确定页码时保留 None，不推算 Word 或 Markdown 页码。"""

    # PDF 使用 page；Markdown 使用 heading_path；Word 使用 paragraph_index。
    page: Position | None = None
    page_end: Position | None = None
    heading_path: list[NonBlank] = Field(default_factory=list)
    paragraph_index: Position | None = None
    table_index: Position | None = None
    row_start: Position | None = None
    row_end: Position | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> Self:
        for start, end in ((self.page, self.page_end), (self.row_start, self.row_end)):
            if end is not None and (start is None or end < start):
                raise ValueError("范围结束位置需要起始位置，且不能小于起始位置")
        if self.row_start is not None and self.table_index is None:
            raise ValueError("表格行位置必须同时指定 table_index")
        if not (self.page or self.heading_path or self.paragraph_index or self.table_index):
            raise ValueError("至少提供页码、标题路径、段落序号或表格序号之一")
        return self


class TableData(Schema):
    """矩形表格。空单元格用空字符串，无表头时 header 为 None。"""

    # 没有表头时 header 为 None；空单元格统一保存为 ""。
    header: list[str] | None = Field(default=None, min_length=1)
    rows: list[list[str]] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_columns(self) -> Self:
        width = len(self.header) if self.header is not None else len(self.rows[0])
        if width == 0 or any(len(row) != width for row in self.rows):
            raise ValueError("表格必须至少有一列，且表头与每行列数一致")
        return self


class Document(Schema):
    """上传文档的身份信息；doc_id 在上传时生成并在后续流程中复用。"""

    doc_id: NonBlank = Field(default_factory=lambda: uuid4().hex)
    filename: NonBlank
    file_type: Literal["pdf", "docx", "md", "xlsx"]


class ParsedBlock(Schema):
    """未切片的原文块。文本块保存正文，表格块保存结构化表格。"""

    # block_id 和 chunk_id 自动生成，用于追踪来源。
    block_id: NonBlank = Field(default_factory=lambda: uuid4().hex)
    doc_id: NonBlank
    kind: Literal["text", "table"]
    location: Location
    text: str = ""
    table: TableData | None = None

    @model_validator(mode="after")
    def validate_content(self) -> Self:
        if self.kind == "text":
            if not self.text.strip() or self.table is not None:
                raise ValueError("文本块需要非空正文，且不能携带 table")
        elif self.table is None:
            raise ValueError("表格块必须携带结构化 table")
        return self


class Chunk(Schema):
    """检索切片。表格 text 由切块器生成，包含表头（若有）及行内容。"""

    # 这是最终送给 Embedding 和向量数据库的对象。
    chunk_id: NonBlank = Field(default_factory=lambda: uuid4().hex)
    doc_id: NonBlank
    filename: NonBlank
    kind: Literal["text", "table"]
    text: Annotated[str, StringConstraints(min_length=1)]
    location: Location
    source_block_ids: list[NonBlank] = Field(min_length=1)
    table: TableData | None = None

    @model_validator(mode="after")
    def validate_source_and_content(self) -> Self:
        if not self.text.strip():
            raise ValueError("切片正文不能为空白")
        if len(set(self.source_block_ids)) != len(self.source_block_ids):
            raise ValueError("source_block_ids 不能重复")
        if (self.kind == "table") != (self.table is not None):
            raise ValueError("表格切片必须携带 table，文本切片不能携带 table")
        return self
