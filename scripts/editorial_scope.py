"""Editorial scope seed: summary and pending work (counts only, never ratios).

uv run python scripts/editorial_scope.py           # human summary (Japanese labels)
uv run python scripts/editorial_scope.py --json    # machine-readable summary
uv run python scripts/editorial_scope.py pending   # candidates and held members

See docs/editorial-scope.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from optimization_compass.editorial_scope import (
    SCOPE_SEED_PATH,
    EditorialScope,
    load_editorial_scope,
    pending_members,
    scope_summary,
)

ROOT = Path(__file__).parents[1]

UNIT_LABELS = {"knowledge_topic": "知識トピック", "problem_structure": "問題構造"}
DECISION_LABELS = {"include": "採用", "merge": "統合", "hold": "保留", "exclude": "除外"}
KIND_LABELS = {
    "algorithm": "アルゴリズム",
    "variant": "変種",
    "strategy": "戦略",
    "primitive": "部品",
    "problem_archetype": "問題原型",
    "modeling_profile": "モデリング型",
    "neighboring_problem": "隣接問題",
}
TIER_LABELS = {"core": "中核", "applied": "応用", "frontier": "先端"}
RELATION_LABELS = {
    "same_entity": "同一の実体",
    "alias_of": "別名",
    "variant_of": "変種",
    "primitive_in": "部品として内包",
    "covered_by_family": "族でのみ網羅",
    "concept_content": "記事で説明",
    "unrepresented": "未表現",
    "unknown": "未照合",
}
REVIEW_LABELS = {"candidate": "候補", "reviewed": "確認済み"}


def _table(title: str, counts: dict[str, int], labels: dict[str, str]) -> list[str]:
    if not counts:
        return [f"  {title}: -"]
    cells = ", ".join(f"{labels.get(key, key)} {value}" for key, value in counts.items())
    return [f"  {title}: {cells}"]


def render(scope: EditorialScope) -> str:
    summary = scope_summary(scope)
    lines = [
        f"{summary['scope_version']} ({summary['status']}) based_on={summary['based_on']}",
        f"メンバー数: {summary['members']}",
    ]
    for unit, data in summary["units"].items():
        included = data["included"]
        lines.append("")
        lines.append(f"[{UNIT_LABELS[unit]}] {data['members']}件")
        lines += _table("判断", data["decision"], DECISION_LABELS)
        lines += _table("採用の種別", included["entity_kind"], KIND_LABELS)
        lines += _table("採用の層", included["tier"], TIER_LABELS)
        lines += _table("採用の対応づけ", included["relation"], RELATION_LABELS)
        lines += _table("採用の確認状態", included["review"], REVIEW_LABELS)
        lines.append(f"  未照合: {data['unreconciled']}, 未表現: {data['unrepresented']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("command", nargs="?", choices=["pending"])
    args = parser.parse_args(argv)
    path = ROOT / SCOPE_SEED_PATH
    if not path.exists():
        print(f"{SCOPE_SEED_PATH} is absent", file=sys.stderr)
        return 1
    scope = load_editorial_scope(path)
    if args.command == "pending":
        rows = pending_members(scope)
        if args.json:
            print(
                json.dumps([m.model_dump(mode="json") for m in rows], ensure_ascii=False, indent=2)
            )
        else:
            for m in rows:
                print(
                    f"{m.scope_id}\t{m.title_ja}\tdecision={m.decision}\t"
                    f"relation={m.mapping.relation}\treview={m.mapping.review}"
                )
            print(f"{len(rows)} pending")
        return 0
    if args.json:
        print(json.dumps(scope_summary(scope), ensure_ascii=False, indent=2))
    else:
        print(render(scope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
