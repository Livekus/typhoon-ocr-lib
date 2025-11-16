from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import json
import pytest
from pytest import CaptureFixture

from typhoon_ocr_lib import cli as cli_mod


class FakeResponse:
    def __init__(
        self,
        source_path: Path,
        task_type: str,
        markdown: str,
        page_num: Optional[int] = None,
    ) -> None:
        self.source_path = source_path
        self.task_type = task_type
        self.markdown = markdown
        self.page_num = page_num


class FakeClient:
    def __init__(self, api_key: Optional[str], default_task_type: str) -> None:
        self.api_key = api_key
        self.default_task_type = default_task_type
        self.calls: list[dict[str, Any]] = []

    def ocr(
        self,
        path: Path,
        task_type: Optional[str] = None,
        page_num: Optional[int] = None,
    ) -> FakeResponse:
        self.calls.append(
            {
                "path": path,
                "task_type": task_type,
                "page_num": page_num,
            }
        )
        markdown = f"# fake {task_type or self.default_task_type}\n\npath={path}"
        return FakeResponse(
            source_path=path,
            task_type=task_type or self.default_task_type,
            markdown=markdown,
            page_num=page_num,
        )


def test_cli_outputs_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    fake_client = FakeClient(api_key="cli-key", default_task_type="structure")

    monkeypatch.setattr(
        "typhoon_ocr_lib.cli.OCRClient",
        lambda api_key, default_task_type: fake_client,
        raising=True,
    )

    cli_mod.main(
        [
            str(pdf),
            "--api-key",
            "cli-key",
            "--task-type",
            "default",
            "--format",
            "md",
        ]
    )

    out = capsys.readouterr().out
    assert "# fake default" in out
    assert "path=" in out

    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["path"] == pdf
    assert call["task_type"] == "default"
    assert call["page_num"] is None


def test_cli_outputs_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    fake_client = FakeClient(api_key="cli-key", default_task_type="structure")

    monkeypatch.setattr(
        "typhoon_ocr_lib.cli.OCRClient",
        lambda api_key, default_task_type: fake_client,
        raising=True,
    )

    cli_mod.main(
        [
            str(pdf),
            "--api-key",
            "cli-key",
            "--task-type",
            "structure",
            "--format",
            "json",
            "--page-num",
            "5",
        ]
    )

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert payload["source_path"] == str(pdf)
    assert payload["task_type"] == "structure"
    assert payload["page_num"] == 5
    assert "# fake structure" in payload["markdown"]


def test_cli_exits_with_error_on_exception(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy", encoding="utf-8")

    class FailingClient:
        def __init__(self, api_key: str | None, default_task_type: str) -> None:
            pass

        def ocr(self, path: Path, task_type: str | None = None, page_num: int | None = None):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "typhoon_ocr_lib.cli.OCRClient",
        FailingClient,
        raising=True,
    )

    with pytest.raises(SystemExit) as excinfo:
        cli_mod.main(
            [
                str(pdf),
                "--api-key",
                "cli-key",
            ]
        )

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    err = captured.err + captured.out
    assert "ERROR:" in err
    assert "boom" in err
