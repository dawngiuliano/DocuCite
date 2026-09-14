"""在终端查看真实样例文件生成的 Chunk。

示例：

    python tests/show_chunks.py
    python tests/show_chunks.py ../data/samples/excel/招聘教师岗位汇总表.xlsx
    python tests/show_chunks.py ../data/samples/markdown/公告.md --limit 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from docucite.chunking import chunk_blocks  # noqa: E402
from docucite.ingest import parse_document  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="查看样例文件生成的检索切片")
    parser.add_argument(
        "file",
        nargs="?",
        help="要查看的文件；不填写时查看 data/samples 下的所有支持文件",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="每个文件最多显示多少个切片，默认 10；设置为 0 表示全部显示",
    )
    args = parser.parse_args()

    if args.limit < 0:
        parser.error("--limit 不能小于 0")

    if args.file:
        files = [Path(args.file)]
    else:
        samples_dir = BACKEND_DIR.parent / "data" / "samples"
        files = sorted(
            path
            for path in samples_dir.rglob("*")
            if path.suffix.lower() in {".md", ".docx", ".xlsx", ".pdf"}
        )

    for path in files:
        print(f"\n{'=' * 80}\n文件: {path}")
        document, blocks = parse_document(path)
        chunks = chunk_blocks(document, blocks)
        shown_chunks = chunks if args.limit == 0 else chunks[: args.limit]
        print(f"解析块: {len(blocks)} 个，切片: {len(chunks)} 个，显示: {len(shown_chunks)} 个")

        for index, chunk in enumerate(shown_chunks, start=1):
            print(f"\n--- Chunk {index} ---")
            print(f"类型: {chunk.kind}")
            print(f"位置: {chunk.location.model_dump(exclude_none=True)}")
            print(f"来源块: {chunk.source_block_ids}")
            print(f"正文:\n{chunk.text}")


if __name__ == "__main__":
    main()
