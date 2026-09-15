"""API 使用的文档、索引和问答服务。"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from threading import RLock
from uuid import uuid4

from ..chain import AnswerResult, GroundedQA
from ..chunking import chunk_blocks
from ..index import EmbeddingClient, FaissStore
from ..index.metadata import load_metadata
from ..ingest import parse_document
from .models import DocumentSummary, UploadResponse


SUPPORTED_SUFFIXES = frozenset({".pdf", ".docx", ".md", ".xlsx"})
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


class DocumentService:
    """管理上传文件、向量索引和问答链。

    默认目录根据本文件位置计算，因此从哪个工作目录启动 FastAPI 都可以找到
    仓库根目录的 data/uploads 和 data/indexes。
    """

    def __init__(
        self,
        upload_dir: str | Path | None = None,
        index_dir: str | Path | None = None,
    ):
        repository_dir = Path(__file__).resolve().parents[3]
        self.upload_dir = Path(upload_dir or repository_dir / "data" / "uploads")
        self.index_dir = Path(index_dir or repository_dir / "data" / "indexes")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_client = None
        self._qa_cache: dict[tuple[int, float], GroundedQA] = {}
        self._lock = RLock()

    def _get_embedding_client(self) -> EmbeddingClient:
        if self._embedding_client is None:
            self._embedding_client = EmbeddingClient()
        return self._embedding_client

    def upload(self, filename: str, content: bytes) -> UploadResponse:
        """保存文件、解析切块并追加到当前索引。"""
        original_name = Path(filename).name
        suffix = Path(original_name).suffix.lower()
        if not original_name or suffix not in SUPPORTED_SUFFIXES:
            raise ValueError("只支持 PDF、Word、Markdown 和 Excel 文件")
        if not content:
            raise ValueError("上传文件不能为空")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError("上传文件不能超过 50 MB")

        stored_path = self.upload_dir / f"{uuid4().hex}{suffix}"
        stored_path.write_bytes(content)
        try:
            document, blocks = parse_document(stored_path)
            # 内部文件名使用 UUID 避免覆盖，引用中仍显示用户上传的原始文件名。
            document.filename = original_name
            chunks = chunk_blocks(document, blocks)
            if not chunks:
                raise ValueError("文件中没有可建立索引的内容")

            with self._lock:
                embed = self._get_embedding_client().embed
                index_path = self.index_dir / "index.faiss"
                metadata_path = self.index_dir / "metadata.json"
                if index_path.exists() != metadata_path.exists():
                    raise RuntimeError("index.faiss 和 metadata.json 不完整，无法追加索引")
                if index_path.exists():
                    store = FaissStore.load(self.index_dir)
                    store.add(chunks, embed)
                else:
                    store = FaissStore.build(chunks, embed)
                store.save(self.index_dir)
                self._qa_cache.clear()
            return UploadResponse(
                doc_id=document.doc_id,
                filename=document.filename,
                file_type=document.file_type,
                block_count=len(blocks),
                chunk_count=len(chunks),
            )
        except Exception:
            stored_path.unlink(missing_ok=True)
            raise

    def list_documents(self) -> list[DocumentSummary]:
        """根据 metadata.json 汇总索引中的文件。"""
        metadata_path = self.index_dir / "metadata.json"
        if not metadata_path.exists():
            return []
        chunks = load_metadata(metadata_path)
        counts: dict[str, int] = defaultdict(int)
        for chunk in chunks:
            counts[chunk.filename] += 1
        return [
            DocumentSummary(
                filename=filename,
                file_type=Path(filename).suffix.lower().lstrip("."),
                chunk_count=counts[filename],
            )
            for filename in sorted(counts, key=str.casefold)
        ]

    def ask(self, question: str, top_k: int = 5, min_score: float = 0.3) -> AnswerResult:
        """使用当前索引回答问题。"""
        index_path = self.index_dir / "index.faiss"
        metadata_path = self.index_dir / "metadata.json"
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("尚未建立索引，请先上传文档或运行 build_index.py")
        cache_key = (top_k, min_score)
        with self._lock:
            qa = self._qa_cache.get(cache_key)
            if qa is None:
                qa = GroundedQA.from_directory(
                    self.index_dir,
                    top_k=top_k,
                    min_score=min_score,
                )
                self._qa_cache[cache_key] = qa
        return qa.ask(question)
