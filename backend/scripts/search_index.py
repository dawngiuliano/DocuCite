"""从已保存的 FAISS 索引中检索相关文档切片。

在 backend/ 目录执行：

    python scripts/search_index.py "教师岗位招聘人数是多少？"
    python scripts/search_index.py "考察和体检安排在什么时间？" --top-k 3
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = BACKEND_DIR.parent
DEFAULT_INDEX_DIR = REPOSITORY_DIR / "data" / "indexes"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from docucite.index import IndexRetriever  # noqa: E402


def create_parser() -> argparse.ArgumentParser:
    """创建查询命令行参数。"""
    parser = argparse.ArgumentParser(description="从 FAISS 索引中检索相关文档切片")
    parser.add_argument("question", help="要检索的问题")
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help="索引目录，默认 ../data/indexes",
    )
    parser.add_argument("--top-k", type=int, default=5, help="返回结果数量，默认 5")
    return parser


def format_location(location) -> str:
    """把 Location 转成适合终端阅读的文字。"""
    values = location.model_dump(exclude_none=True)
    if not values:
        return "未知位置"
    return ", ".join(f"{key}={value}" for key, value in values.items())


def main(argv: Sequence[str] | None = None) -> int:
    """执行一次查询并打印引用信息。"""
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.top_k <= 0:
        parser.error("--top-k 必须大于 0")

    try:
        retriever = IndexRetriever.from_directory(args.index_dir)
        results = retriever.search(args.question, top_k=args.top_k)
    except (FileNotFoundError, ValueError, ModuleNotFoundError, OSError) as error:
        print(f"检索失败: {error}", file=sys.stderr)
        return 1

    if not results:
        print("没有找到相关切片。")
        return 0

    print(f"问题: {args.question}")
    print(f"返回 {len(results)} 条结果：")
    for rank, result in enumerate(results, start=1):
        chunk = result.chunk
        print(f"\n[{rank}] 相似度: {result.score:.4f}")
        print(f"文件: {chunk.filename}")
        print(f"类型: {chunk.kind}")
        print(f"位置: {format_location(chunk.location)}")
        print(f"来源块: {', '.join(chunk.source_block_ids)}")
        print(f"正文:\n{chunk.text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
