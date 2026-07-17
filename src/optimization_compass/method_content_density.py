from __future__ import annotations

import re
from dataclasses import dataclass

from optimization_compass.content_models import ContentPage

PYTHON_BLOCK_PATTERN = re.compile(r"^```python\n(.*?)^```$", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class DensityRow:
    content_id: str
    method_id: str
    summary_characters: int
    body_characters: int
    toc_entries: int
    python_blocks: int
    compile_errors: tuple[str, ...]

    @property
    def meets_floor(self) -> bool:
        return (
            self.summary_characters >= 35
            and self.body_characters >= 1_200
            and self.toc_entries >= 4
            and self.python_blocks >= 1
            and not self.compile_errors
        )


def inspect_page(page: ContentPage) -> DensityRow:
    blocks = PYTHON_BLOCK_PATTERN.findall(page.body)
    errors: list[str] = []
    for index, block in enumerate(blocks, start=1):
        try:
            compile(block, f"{page.content_id}:python:{index}", "exec")
        except SyntaxError as error:
            errors.append(f"block {index}: {error.msg} at line {error.lineno}")
    return DensityRow(
        content_id=page.content_id,
        method_id=page.method_id or "",
        summary_characters=len(page.summary),
        body_characters=len(page.body),
        toc_entries=len(page.toc),
        python_blocks=len(blocks),
        compile_errors=tuple(errors),
    )


def render_report(rows: list[DensityRow]) -> str:
    passing = sum(row.meets_floor for row in rows)
    lines = [
        "# Method content density report",
        "",
        f"- Published method guides: `{len(rows)}`",
        f"- Meeting the Level 2 floor: `{passing}`",
        f"- Below the floor: `{len(rows) - passing}`",
        "",
        "| Content | Method | Summary | Body | TOC | Python | Result |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        result = "pass" if row.meets_floor else "fail"
        if row.compile_errors:
            result += ": " + "; ".join(row.compile_errors)
        lines.append(
            f"| `{row.content_id}` | `{row.method_id}` | {row.summary_characters} | "
            f"{row.body_characters} | {row.toc_entries} | {row.python_blocks} | {result} |"
        )
    lines.extend(
        [
            "",
            "## Floor",
            "",
            "- summary: at least 35 characters",
            "- body: at least 1,200 characters",
            "- table of contents: at least 4 entries",
            "- at least one syntactically valid Python block",
            "",
            (
                "The floor prevents visibly empty pages. It is not a quality ranking and does "
                "not require every method to have visualization or comparison artifacts."
            ),
            "",
        ]
    )
    return "\n".join(lines)
