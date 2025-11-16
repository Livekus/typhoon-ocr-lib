from pathlib import Path
from typing import Any, Dict, List

import os
import pytest

from typhoon_ocr_lib.client import OCRClient
from typhoon_ocr_lib.models import OCRResponse


def test_client_init_uses_api_key_argument(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TYPHOON_OCR_API_KEY", raising=False)

    client = OCRClient(api_key="dummy-key")

    assert client.api_key == "dummy-key"
    assert os.environ["TYPHOON_OCR_API_KEY"] == "dummy-key"


def test_client_init_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TYPHOON_OCR_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        OCRClient()

    assert "API key not set" in str(excinfo.value)


def test_ocr_calls_underlying_ocr_document(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    calls: List[Dict[str, Any]] = []

    def fake_ocr_document(pdf_or_image_path: str, task_type: str, page_num: int | None):
        calls.append(
            {
                "pdf_or_image_path": pdf_or_image_path,
                "task_type": task_type,
                "page_num": page_num,
            }
        )
        return f"# OCR({task_type}) page={page_num} :: {pdf_or_image_path}"

    monkeypatch.setattr(
        "typhoon_ocr_lib.client.ocr_document",
        fake_ocr_document,
        raising=True,
    )

    client = OCRClient(api_key="dummy-key", default_task_type="structure")

    res: OCRResponse = client.ocr(
        path=pdf,
        task_type="default",
        page_num=2,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call["pdf_or_image_path"] == str(pdf)
    assert call["task_type"] == "default"
    assert call["page_num"] == 2

    assert isinstance(res, OCRResponse)
    assert res.source_path == pdf
    assert res.task_type == "default"
    assert "# OCR(default)" in res.markdown
    assert res.page_num == 2


def test_ocr_uses_default_task_type_when_not_provided(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    captured: dict | None = None

    def fake_ocr_document(pdf_or_image_path: str, task_type: str, page_num: int | None):
        nonlocal captured
        captured = {
            "pdf_or_image_path": pdf_or_image_path,
            "task_type": task_type,
            "page_num": page_num,
        }
        return "ok"

    monkeypatch.setattr(
        "typhoon_ocr_lib.client.ocr_document",
        fake_ocr_document,
        raising=True,
    )

    client = OCRClient(api_key="dummy-key", default_task_type="structure")
    res = client.ocr(path=pdf)

    assert captured is not None
    assert captured["task_type"] == "structure"
    assert res.task_type == "structure"
    assert res.page_num is None
