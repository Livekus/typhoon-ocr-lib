from pathlib import Path

import pytest

from typhoon_ocr_lib.models import OCRRequest, OCRResponse


def test_ocr_request_accepts_existing_path(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    req = OCRRequest(path=pdf, task_type="default")

    assert req.path == pdf
    assert req.task_type == "default"


def test_ocr_request_rejects_missing_path(tmp_path: Path) -> None:
    pdf = tmp_path / "missing.pdf"  # not created

    with pytest.raises(ValueError) as excinfo:
        OCRRequest(path=pdf, task_type="structure")

    assert "Input path does not exist" in str(excinfo.value)


def test_ocr_response_simple_roundtrip(tmp_path: Path) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    res = OCRResponse(
        source_path=pdf,
        task_type="structure",
        markdown="# Title\n\ncontent",
        page_num=3,
    )

    assert res.source_path == pdf
    assert res.task_type == "structure"
    assert "Title" in res.markdown
    assert res.page_num == 3
