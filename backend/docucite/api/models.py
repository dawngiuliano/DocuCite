"""FastAPI 请求和响应模型。"""

from pydantic import Field

from ..chain import AnswerResult
from ..schemas import NonBlank, Schema


class UploadResponse(Schema):
    """上传并建立索引后的结果。"""

    doc_id: NonBlank
    filename: NonBlank
    file_type: NonBlank
    block_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)


class DocumentSummary(Schema):
    """索引中的一份文档摘要。"""

    filename: NonBlank
    file_type: NonBlank
    chunk_count: int = Field(ge=0)


class AskRequest(Schema):
    """提问请求。"""

    question: NonBlank
    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.3, ge=-1, le=1)


AskResponse = AnswerResult
