from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

import pytest
from pytest import CaptureFixture

from typhoon_ocr_lib import cli as cli_mod


# E2E-ish: CLI -> OCRClient -> fake ocr_document, in a single process.
@pytest.mark.e2e
def test_cli_e2e_fake_backend(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    # Fake backend that simulates typhoon_ocr.ocr_document
    def fake_ocr_document(
        pdf_or_image_path: str,
        task_type: str,
        page_num: Optional[int],
    ) -> str:
        assert Path(pdf_or_image_path) == pdf
        assert task_type == "default"
        assert page_num == 1
        return "# fake-ocr\n\nok"

    # Make sure the client thinks it has a key
    monkeypatch.setenv("TYPHOON_OCR_API_KEY", "test-key")

    # Patch at the usage site inside our library
    monkeypatch.setattr(
        "typhoon_ocr_lib.client.ocr_document",
        fake_ocr_document,
        raising=True,
    )

    # Call the CLI main directly, as if from the shell
    cli_mod.main(
        [
            str(pdf),
            "--task-type",
            "default",
            "--format",
            "json",
            "--page-num",
            "1",
        ]
    )

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert payload["source_path"] == str(pdf)
    assert payload["task_type"] == "default"
    assert payload["page_num"] == 1
    assert "# fake-ocr" in payload["markdown"]


# True E2E: real Typhoon OCR, still in-process (no monkeypatch).
@pytest.mark.e2e_real
@pytest.mark.skipif(
    not os.getenv("TYPHOON_OCR_API_KEY"),
    reason="TYPHOON_OCR_API_KEY not set; skipping real E2E",
)
def test_cli_e2e_real_backend(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy text", encoding="utf-8")

    # Env var is checked by the client; we do not monkeypatch here.
    assert os.getenv("TYPHOON_OCR_API_KEY")

    cli_mod.main(
        [
            str(pdf),
            "--task-type",
            "structure",
            "--format",
            "json",
        ]
    )

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert payload["source_path"] == str(pdf)
    assert payload["task_type"] == "structure"
    assert isinstance(payload["markdown"], str)
    assert payload["markdown"].strip() != ""
