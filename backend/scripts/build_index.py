"""从文档构建 FAISS 索引。

默认扫描仓库根目录的 ``data/samples``，也可以传入文件或目录：

    python scripts/build_index.py
    python scripts/build_index.py ../data/samples/markdown/公告.md
    python scripts/build_index.py ../data/samples --output ../data/indexes

这个脚本会调用真实的 Embedding API，因此运行前需要配置 backend/.env。
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
import sys


# 允许从 backend/ 目录直接运行：python scripts/build_index.py
BACKEND_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from docucite.chunking import chunk_blocks  # noqa: E402
from docucite.index import EmbeddingClient, FaissStore  # noqa: E402
from docucite.schemas import Chunk  # noqa: E402
from docucite.ingest import parse_document  # noqa: E402


SUPPORTED_SUFFIXES = frozenset({".pdf", ".docx", ".md", ".xlsx"})
DEFAULT_SOURCE = REPOSITORY_DIR / "data" / "samples"
DEFAULT_OUTPUT = REPOSITORY_DIR / "data" / "indexes"


@dataclass(frozen=True)
class BuildSummary:
    """一次构建的统计信息。"""

    files: int
    blocks: int
    chunks: int
    output_dir: Path


def collect_files(sources: Sequence[str | Path] | None = None) -> list[Path]:
    """收集待处理文件，支持文件、目录和默认样例目录。

    目录会递归查找四种支持的扩展名；文件路径如果不是支持格式会直接报错，
    避免用户以为某个文件已经被加入索引。
    """
    raw_sources: Iterable[str | Path] = sources or [DEFAULT_SOURCE]
    collected: dict[str, Path] = {}

    for raw_source in raw_sources:
        source = Path(raw_source).expanduser()
        if not source.exists():
            raise FileNotFoundError(f"找不到输入路径: {source}")

        if source.is_file():
            if source.suffix.lower() not in SUPPORTED_SUFFIXES:
                raise ValueError(f"不支持的文件类型: {source.suffix}，支持 PDF、Word、Markdown、Excel")
            resolved = source.resolve()
            collected[str(resolved).casefold()] = resolved
            continue

        for path in source.rglob("*"):
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
                resolved = path.resolve()
                collected[str(resolved).casefold()] = resolved

    files = sorted(collected.values(), key=lambda path: str(path).casefold())
    if not files:
        raise ValueError("输入路径中没有找到 PDF、Word、Markdown 或 Excel 文件")
    return files


def collect_chunks(
    files: Sequence[Path],
    *,
    max_chars: int = 1000,
    overlap: int = 100,
) -> tuple[list[Chunk], int]:
    """解析并切分所有文件，返回切片和解析块总数。"""
    all_chunks: list[Chunk] = []
    total_blocks = 0
    for path in files:
        try:
            document, blocks = parse_document(path)
            chunks = chunk_blocks(document, blocks, max_chars=max_chars, overlap=overlap)
        except Exception as error:
            raise RuntimeError(f"处理文件失败: {path}\n{type(error).__name__}: {error}") from error
        total_blocks += len(blocks)
        all_chunks.extend(chunks)
    if not all_chunks:
        raise ValueError("文件解析成功，但没有生成可建立索引的切片")
    return all_chunks, total_blocks


def build_index(
    sources: Sequence[str | Path] | None = None,
    *,
    output_dir: str | Path = DEFAULT_OUTPUT,
    max_chars: int = 1000,
    overlap: int = 100,
    embed: Callable[[list[str]], list[list[float]]] | None = None,
) -> BuildSummary:
    """执行“收集 -> 解析 -> 切块 -> 向量化 -> 保存”的完整流程。

    ``embed`` 主要用于测试；正常运行时省略它，脚本会使用 .env 中配置的
    EmbeddingClient。保存操作会覆盖输出目录中的同名 index.faiss 和 metadata.json。
    """
    files = collect_files(sources)
    chunks, total_blocks = collect_chunks(files, max_chars=max_chars, overlap=overlap)
    embed_function = embed or EmbeddingClient().embed
    store = FaissStore.build(chunks, embed_function)
    target = Path(output_dir).expanduser().resolve()
    store.save(target)
    return BuildSummary(
        files=len(files),
        blocks=total_blocks,
        chunks=len(chunks),
        output_dir=target,
    )


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="解析文档并构建 FAISS 向量索引")
    parser.add_argument(
        "sources",
        nargs="*",
        help="输入文件或目录；不填写时默认扫描 ../data/samples",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="索引输出目录，默认 ../data/indexes",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=1000,
        help="文本切片最大字符数，默认 1000",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=100,
        help="相邻文本切片的重叠字符数，默认 100",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """命令行入口。"""
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.max_chars <= 0:
        parser.error("--max-chars 必须大于 0")
    if args.overlap < 0 or args.overlap >= args.max_chars:
        parser.error("--overlap 必须大于等于 0 且小于 --max-chars")

    try:
        summary = build_index(
            args.sources or None,
            output_dir=args.output,
            max_chars=args.max_chars,
            overlap=args.overlap,
        )
    except (FileNotFoundError, ValueError, RuntimeError, ModuleNotFoundError) as error:
        print(f"构建失败: {error}", file=sys.stderr)
        return 1

    print(f"已处理文件: {summary.files}")
    print(f"解析块数量: {summary.blocks}")
    print(f"检索切片数量: {summary.chunks}")
    print(f"索引目录: {summary.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
