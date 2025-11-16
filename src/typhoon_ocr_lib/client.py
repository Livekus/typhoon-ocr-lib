from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from typhoon_ocr import ocr_document

from .models import OCRRequest, OCRResponse, TaskType


class OCRClient:
    """
    High-level wrapper around the official `typhoon-ocr` package.

    It:
    - Manages API key via env or constructor.
    - Exposes a simple, typed `.ocr()` method.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_task_type: TaskType = "structure",
    ) -> None:
        # Typhoon OCR package reads TYPHOON_OCR_API_KEY from env.
        self.api_key = api_key or os.getenv("TYPHOON_OCR_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Typhoon OCR API key not set. "
                "Pass api_key=... or export TYPHOON_OCR_API_KEY."
            )

        # Ensure env is set for the underlying package.
        os.environ.setdefault("TYPHOON_OCR_API_KEY", self.api_key)

        self.default_task_type = default_task_type

    @classmethod
    def from_env(cls, default_task_type: TaskType = "structure") -> "OCRClient":
        """
        Construct a client using TYPHOON_OCR_API_KEY from the environment.
        """
        return cls(api_key=None, default_task_type=default_task_type)

    def ocr(
        self,
        path: str | Path,
        task_type: Optional[TaskType] = None,
        page_num: Optional[int] = None,
    ) -> OCRResponse:
        """
        Run OCR on a single PDF/image.

        - If `page_num` is None, delegate the default behavior to typhoon-ocr.
        - If set, ask Typhoon OCR for that specific page (when supported).
        """
        req = OCRRequest(
            path=Path(path),
            task_type=task_type or self.default_task_type,
        )

        markdown = ocr_document(
            pdf_or_image_path=str(req.path),
            task_type=req.task_type,
            page_num=page_num,
        )

        return OCRResponse(
            source_path=req.path,
            task_type=req.task_type,
            markdown=markdown,
            page_num=page_num,
        )
