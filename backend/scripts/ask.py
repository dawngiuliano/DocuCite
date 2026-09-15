"""通过检索增强问答链回答问题。

在 backend/ 目录执行：

    python scripts/ask.py "教师岗位招聘人数是多少？"
    python scripts/ask.py "考察和体检安排在什么时间？" --top-k 3 --min-score 0.25
    python scripts/ask.py "教师岗位招聘人数是多少？" --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPOSITORY_DIR = BACKEND_DIR.parent
DEFAULT_INDEX_DIR = REPOSITORY_DIR / "data" / "indexes"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from docucite.chain import GroundedQA  # noqa: E402


def create_parser() -> argparse.ArgumentParser:
    """创建问答命令行参数。"""
    parser = argparse.ArgumentParser(description="根据文档索引回答问题并返回引用")
    parser.add_argument("question", help="要提问的问题")
    parser.add_argument(
        "--index-dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        help="索引目录，默认 ../data/indexes",
    )
    parser.add_argument("--top-k", type=int, default=5, help="最多使用多少个检索切片，默认 5")
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.3,
        help="最低相似度，低于此值时拒绝回答，默认 0.3",
    )
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """执行一次问答。"""
    parser = create_parser()
    args = parser.parse_args(argv)
    if args.top_k <= 0:
        parser.error("--top-k 必须大于 0")
    if not -1 <= args.min_score <= 1:
        parser.error("--min-score 必须在 -1 和 1 之间")

    try:
        qa = GroundedQA.from_directory(
            args.index_dir,
            top_k=args.top_k,
            min_score=args.min_score,
        )
        result = qa.ask(args.question)
    except (FileNotFoundError, ValueError, ModuleNotFoundError, OSError) as error:
        print(f"问答失败: {error}", file=sys.stderr)
        return 1

    if args.json:
        print(result.model_dump_json(indent=2))
        return 0

    print(f"问题: {args.question}")
    print(f"答案: {result.answer}")
    if not result.citations:
        print("引用: 无（检索结果不足）")
        return 0

    print("引用:")
    for number, citation in enumerate(result.citations, start=1):
        location = citation.location.model_dump(exclude_none=True)
        print(f"\n[{number}] {citation.filename}，相似度 {citation.score:.4f}")
        print(f"位置: {location}")
        print(f"片段: {citation.snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
