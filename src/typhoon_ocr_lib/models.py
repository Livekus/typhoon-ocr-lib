from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


TaskType = Literal["default", "structure"]


class OCRRequest(BaseModel):
    path: Path = Field(..., description="Path to PDF or image.")
    task_type: TaskType = Field(
        "structure",
        description='Typhoon OCR task type: "default" or "structure".',
    )

    @field_validator("path")
    @classmethod
    def _check_path_exists(cls, p: Path) -> Path:
        if not p.exists():
            raise ValueError(f"Input path does not exist: {p}")
        return p


class OCRResponse(BaseModel):
    source_path: Path
    task_type: TaskType
    markdown: str
    page_num: Optional[int] = Field(
        None, description="Optional page number if you handled per-page OCR."
    )
