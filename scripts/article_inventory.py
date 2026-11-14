"""One row per published article, to choose which article to work on next.

uv run python scripts/article_inventory.py                # learning paths first, then no figure
uv run python scripts/article_inventory.py --kind method  # formulation / method / family / concept
uv run python scripts/article_inventory.py --ids adam,bfgs
uv run python scripts/article_inventory.py --json
uv run python scripts/article_inventory.py --figure-text  # text size of static SVGs as displayed
uv run python scripts/article_inventory.py --approve adam # only when the owner said so (see below)

Columns: whether a learning path (data/seeds/learning_paths.json) steps through the article, its
kind and entity, body characters, static figures, explorables (``*`` when the explorable has
guided beats in its figure folder's meta.json), the owner's approval
(``approved``, or ``changed`` when the body was edited after the approval), and last_reviewed.

``--figure-text`` lists every static SVG the selected articles show, with the smallest and largest
text size a reader sees on a PC and on a 375 px phone (353 px of article width). Figures under
``figures/`` are shown at most 440 px wide and figures under ``media/`` at most 672 px; text
should read at 12 px or more on the phone and no more than 18 px on the PC.

This is an inventory, not a gate: nothing here fails a build.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from optimization_compass.content_models import (
    ArticleKind,
    ContentPage,
    article_kind,
    load_content,
)
from optimization_compass.content_quality import FigureText, figure_text, static_svg_paths
from optimization_compass.explorables import load_explorables
from optimization_compass.owner_approvals import (
    ApprovalState,
    approval_state,
    load_owner_approvals,
    record_owner_approval,
)

ROOT = Path(__file__).parents[1]
KINDS: tuple[ArticleKind, ...] = ("formulation", "method", "family", "concept")
_IMAGE = re.compile(r"^!\[", re.MULTILINE)
_EXPLORABLE = re.compile(r"^::: explorable (\S+)", re.MULTILINE)
APPROVE_HELP = (
    "record that the owner approved this article's current body; run it only when the owner "
    "says they approved the article on screen, never on your own judgement"
)


@dataclass(frozen=True)
class InventoryRow:
    content_id: str
    title_ja: str
    kind: ArticleKind
    entity_id: str
    on_path: bool
    body_characters: int
    static_figures: int
    explorables: tuple[str, ...]
    explorables_with_beats: tuple[str, ...]
    owner: ApprovalState | None
    last_reviewed: str | None

    @property
    def visuals(self) -> int:
        return self.static_figures + len(self.explorables)


def learning_path_targets(root: Path) -> frozenset[str]:
    """Content IDs and formulation IDs (``PAxxx``) that some learning path steps through."""
    raw = json.loads((root / "data/seeds/learning_paths.json").read_text(encoding="utf-8"))
    return frozenset(step["target_id"] for path in raw["paths"] for step in path["steps"])


def inventory_rows(
    pages: Iterable[ContentPage],
    *,
    path_targets: frozenset[str],
    beats: Mapping[str, bool],
    approvals_root: Path,
) -> list[InventoryRow]:
    approvals = load_owner_approvals(approvals_root)
    rows = []
    for page in pages:
        if page.status != "published":
            continue
        kind = article_kind(page)
        explorables = tuple(_EXPLORABLE.findall(page.body))
        rows.append(
            InventoryRow(
                content_id=page.content_id,
                title_ja=page.title_ja,
                kind=kind,
                entity_id=page.method_id or page.canonical_entity_id,
                on_path=page.content_id in path_targets
                or (kind == "formulation" and page.canonical_entity_id in path_targets),
                body_characters=len(page.body),
                static_figures=len(_IMAGE.findall(page.body)),
                explorables=explorables,
                explorables_with_beats=tuple(item for item in explorables if beats.get(item)),
                owner=approval_state(page, approvals),
                last_reviewed=page.last_reviewed,
            )
        )
    return sorted(rows, key=_priority)


def _priority(row: InventoryRow) -> tuple[int, int, int, str]:
    """On a learning path first, then articles without any figure, then the fewest visuals."""
    return (0 if row.on_path else 1, 0 if row.visuals == 0 else 1, row.visuals, row.content_id)


def _explorable_label(row: InventoryRow) -> str:
    beats = set(row.explorables_with_beats)
    return ",".join(f"{item}*" if item in beats else item for item in row.explorables) or "-"


def render_rows(rows: list[InventoryRow]) -> str:
    lines = [
        f"{'path':<5} {'kind':<11} {'figs':>4} {'body':>6} {'owner':<8} {'reviewed':<10} "
        "article (entity)  explorables"
    ]
    for row in rows:
        lines.append(
            f"{'yes' if row.on_path else '-':<5} {row.kind:<11} {row.static_figures:>4} "
            f"{row.body_characters:>6} {row.owner or '-':<8} {row.last_reviewed or '-':<10} "
            f"{row.content_id} ({row.entity_id})  {_explorable_label(row)}"
        )
    without = sum(row.visuals == 0 for row in rows)
    approved = sum(row.owner == "approved" for row in rows)
    changed = sum(row.owner == "changed" for row in rows)
    lines.append(
        f"{len(rows)} articles: {sum(row.on_path for row in rows)} on a learning path, "
        f"{without} with no static figure or explorable, "
        f"owner approved {approved} (changed since: {changed})"
    )
    return "\n".join(lines)


def render_figure_text(results: list[FigureText]) -> str:
    lines = ["PC        phone     verdict  figure"]
    for item in results:
        pc = f"{item.pc[0]:.0f}-{item.pc[1]:.0f}px" if item.pc else "?"
        phone = f"{item.phone[0]:.0f}-{item.phone[1]:.0f}px" if item.phone else "?"
        verdict = "ok" if item.readable else ("unknown" if item.pc is None else "fix")
        lines.append(f"{pc:<9} {phone:<9} {verdict:<8} {item.path}")
    fixes = sum(not item.readable for item in results)
    lines.append(f"{len(results) - fixes} ok / {fixes} to fix (total {len(results)})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--kind", choices=KINDS, help="only this kind of article")
    parser.add_argument("--ids", default="", help="comma-separated content IDs")
    parser.add_argument("--json", action="store_true", help="print the rows as JSON")
    parser.add_argument("--figure-text", action="store_true", help="SVG text size as displayed")
    parser.add_argument("--approve", metavar="CONTENT_ID", help=APPROVE_HELP)
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    pages = [page for page in load_content(ROOT / "content") if page.status == "published"]
    if args.approve:
        page = next((item for item in pages if item.content_id == args.approve), None)
        if page is None:
            print(f"{args.approve} is not a published article", file=sys.stderr)
            return 1
        approval = record_owner_approval(ROOT, page, approved_on=date.today())
        print(f"recorded: {page.content_id} {approval.body_sha256} {approval.approved_on}")
        return 0

    wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
    selected = [
        page
        for page in pages
        if (args.kind is None or article_kind(page) == args.kind)
        and (not wanted or page.content_id in wanted)
    ]
    if args.figure_text:
        refs = sorted({ref for page in selected for ref in static_svg_paths(page)})
        print(render_figure_text([figure_text(ROOT, ref) for ref in refs]))
        return 0
    beats = {item_id: bool(entry.beats) for item_id, entry in load_explorables().items()}
    rows = inventory_rows(
        selected, path_targets=learning_path_targets(ROOT), beats=beats, approvals_root=ROOT
    )
    if args.json:
        print(json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2))
    else:
        print(render_rows(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
