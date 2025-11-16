from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Literal, Optional

from .client import OCRClient
from .models import TaskType


OutputFormat = Literal["md", "json"]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="typhoon-ocr",
        description="CLI wrapper on top of Typhoon OCR.",
    )
    p.add_argument(
        "path",
        type=Path,
        help="Path to PDF or image to OCR.",
    )
    p.add_argument(
        "--api-key",
        dest="api_key",
        default=None,
        help="Typhoon OCR API key (otherwise uses TYPHOON_OCR_API_KEY).",
    )
    p.add_argument(
        "--task-type",
        dest="task_type",
        choices=["default", "structure"],
        default="structure",
        help='Typhoon OCR task type: "default" or "structure".',
    )
    p.add_argument(
        "--page-num",
        dest="page_num",
        type=int,
        default=None,
        help="Optional page number (1-based) to OCR only that page.",
    )
    p.add_argument(
        "--format",
        dest="fmt",
        choices=["md", "json"],
        default="md",
        help="Output format (markdown or JSON wrapper).",
    )
    return p


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    client = OCRClient(api_key=args.api_key, default_task_type=args.task_type)  # type: ignore[arg-type]

    try:
        result = client.ocr(
            path=args.path,
            task_type=args.task_type,  # type: ignore[arg-type]
            page_num=args.page_num,
        )
    except Exception as e:  # noqa: BLE001
        parser.exit(1, f"ERROR: {e}\n")

    if args.fmt == "md":
        sys.stdout.write(result.markdown)
    else:  # json
        payload = {
            "source_path": str(result.source_path),
            "task_type": result.task_type,
            "page_num": result.page_num,
            "markdown": result.markdown,
        }
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
