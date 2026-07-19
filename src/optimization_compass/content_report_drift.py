from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ReportSpec:
    generator: Path
    committed: Path


REPORTS: tuple[ReportSpec, ...] = (
    ReportSpec(
        generator=Path("scripts/content_quality_report.py"),
        committed=Path("docs/content-quality-report.md"),
    ),
    ReportSpec(
        generator=Path("scripts/method_content_density_report.py"),
        committed=Path("docs/method-content-density-report.md"),
    ),
)


class ReportGenerationError(RuntimeError):
    pass


def _normalized_report_bytes(path: Path) -> bytes:
    # Git may check text files out as CRLF on Windows while the official
    # generators deliberately emit LF. Compare repository content, not the
    # checkout's platform line-ending representation.
    return path.read_bytes().replace(b"\r\n", b"\n")


def find_report_drift(
    root: Path = ROOT,
    reports: tuple[ReportSpec, ...] = REPORTS,
) -> tuple[Path, ...]:
    """Regenerate every report through its official script and return stale paths."""
    stale: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="optimization-compass-content-reports-") as raw_temp:
        temporary_root = Path(raw_temp)
        for report in reports:
            generated = temporary_root / report.committed
            generated.parent.mkdir(parents=True, exist_ok=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(root / report.generator),
                    "--output",
                    str(generated),
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0:
                detail = "\n".join(
                    part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
                )
                raise ReportGenerationError(
                    f"{report.generator.as_posix()} failed"
                    + (f":\n{detail}" if detail else f" with exit code {completed.returncode}")
                )
            committed = root / report.committed
            if not committed.is_file() or _normalized_report_bytes(
                committed
            ) != _normalized_report_bytes(generated):
                stale.append(report.committed)
    return tuple(stale)


def main() -> int:
    try:
        stale = find_report_drift()
    except ReportGenerationError as error:
        print(f"Content report generation failed: {error}", file=sys.stderr)
        return 1
    if not stale:
        print(f"Content reports are current ({len(REPORTS)} checked).")
        return 0

    print("Stale generated content reports:", file=sys.stderr)
    for path in stale:
        print(f"- {path.as_posix()}", file=sys.stderr)
    print("\nRegenerate and commit them with:", file=sys.stderr)
    for report in REPORTS:
        print(f"uv run python {report.generator.as_posix()}", file=sys.stderr)
    print(
        "git diff -- docs/content-quality-report.md docs/method-content-density-report.md",
        file=sys.stderr,
    )
    return 1
