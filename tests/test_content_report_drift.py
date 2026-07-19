from __future__ import annotations

from pathlib import Path

import pytest

from optimization_compass.content_report_drift import (
    REPORTS,
    ROOT,
    ReportGenerationError,
    ReportSpec,
    find_report_drift,
)


def _write_generator(path: Path, *, content: str, exit_code: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "from pathlib import Path\n"
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--output', type=Path, required=True)\n"
        "args = parser.parse_args()\n"
        f"args.output.write_text({content!r}, encoding='utf-8', newline='\\n')\n"
        f"raise SystemExit({exit_code})\n",
        encoding="utf-8",
    )


def test_committed_content_reports_match_their_official_generators() -> None:
    assert find_report_drift(ROOT, REPORTS) == ()


def test_report_drift_names_only_stale_outputs(tmp_path: Path) -> None:
    generator = Path("scripts/report.py")
    committed = Path("docs/report.md")
    _write_generator(tmp_path / generator, content="fresh\n")
    (tmp_path / committed).parent.mkdir(parents=True)
    (tmp_path / committed).write_text("stale\n", encoding="utf-8")

    assert find_report_drift(tmp_path, (ReportSpec(generator, committed),)) == (committed,)

    (tmp_path / committed).write_text("fresh\n", encoding="utf-8", newline="\n")
    assert find_report_drift(tmp_path, (ReportSpec(generator, committed),)) == ()

    (tmp_path / committed).write_bytes(b"fresh\r\n")
    assert find_report_drift(tmp_path, (ReportSpec(generator, committed),)) == ()


def test_report_generation_failure_is_not_misreported_as_drift(tmp_path: Path) -> None:
    generator = Path("scripts/report.py")
    _write_generator(tmp_path / generator, content="partial\n", exit_code=7)

    with pytest.raises(ReportGenerationError, match="scripts/report.py failed"):
        find_report_drift(tmp_path, (ReportSpec(generator, Path("docs/report.md")),))
