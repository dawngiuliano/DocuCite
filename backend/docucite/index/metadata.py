"""保存 FAISS 向量对应的 Chunk 元数据。"""

import json
from pathlib import Path

from ..schemas import Chunk


def save_metadata(path: str | Path, chunks: list[Chunk]) -> None:
    """按向量顺序保存切片，后续检索结果可用整数位置反查。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps([chunk.model_dump(mode="json") for chunk in chunks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_metadata(path: str | Path) -> list[Chunk]:
    """从 JSON 恢复切片对象。"""
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Chunk.model_validate(value) for value in values]
