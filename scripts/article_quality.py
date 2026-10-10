"""Article quality ledger: which article meets which criterion, and what is missing or stale.

uv run python scripts/article_quality.py                       # summary of all articles
uv run python scripts/article_quality.py show adam             # one article's checklist
uv run python scripts/article_quality.py next --limit 10       # what to fix or review next
uv run python scripts/article_quality.py criteria              # the criteria and who checks them
uv run python scripts/article_quality.py record adam --reviewer claude --pass all \\
    --fail "pitfalls.with-example=一般論だけで、例の数値がない" --na explorable.ui-names
uv run python scripts/article_quality.py --json [show ID ...]  # machine-readable

States: pass / fail / na / waived (an auto check overruled with a reason); ``unreviewed``
(no review yet), ``stale`` (the body changed after the review), ``new`` (the criterion was
added or tightened after the review). See docs/article-quality.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from optimization_compass.article_quality import (
    ArticleReport,
    Ledger,
    evaluate_all,
    priority,
    record_review,
    review_criteria_for,
)

ROOT = Path(__file__).parents[1]
MARK = {
    "pass": "✓",
    "fail": "✗",
    "na": "-",
    "waived": "w",
    "unreviewed": "?",
    "stale": "~",
    "new": "+",
}


def _report_json(report: ArticleReport) -> dict[str, Any]:
    article = report.article
    return {
        "content_id": article.content_id,
        "path": article.path.as_posix(),
        "kind": article.kind,
        "on_learning_path": article.on_learning_path,
        "status": report.status,
        "reviewer": report.reviewer,
        "reviewed_on": report.review["reviewed_on"] if report.review else None,
        "visual_level": report.visual_level,
        "style_warnings": report.style_warning_count,
        "checks": [
            {"criterion_id": r.criterion_id, "state": r.state, "detail": r.detail}
            for r in report.results
        ],
    }


def _find(reports: tuple[ArticleReport, ...], key: str) -> ArticleReport:
    for report in reports:
        article = report.article
        if key in (article.content_id, article.path.as_posix(), article.path.stem):
            return report
    raise SystemExit(f"unknown article: {key}")


def summary(ledger: Ledger, reports: tuple[ArticleReport, ...]) -> None:
    statuses = Counter(report.status for report in reports)
    print(
        f"記事 {len(reports)}本: "
        + " / ".join(f"{name} {statuses[name]}" for name in ("達成", "要修正", "要レビュー"))
    )
    reviewed = sum(report.review is not None for report in reports)
    owner = sum(report.reviewer == "owner" for report in reports)
    print(f"レビュー済み {reviewed}本（うちオーナー {owner}本）")
    print()
    print("基準ごと（✓pass ✗fail w免除 ?未レビュー ~本文変更後 +基準追加後）")
    for criterion in ledger.criteria:
        states = Counter(
            r.state
            for report in reports
            for r in report.results
            if r.criterion_id == criterion.criterion_id
        )
        counts = " ".join(f"{MARK[s]}{states[s]}" for s in MARK if states[s] and s != "na")
        print(f"  {criterion.check:<6} {criterion.criterion_id:<28} {counts}")
    print()
    print("状態     種類        経路 図          記事")
    for report in sorted(reports, key=priority):
        article = report.article
        marks = "".join(MARK[r.state] for r in report.results)
        path_mark = "●" if article.on_learning_path else " "
        print(
            f"{report.status:<6} {article.kind:<11} {path_mark}  {report.visual_level:<11} "
            f"{article.content_id}  {marks}"
        )


def show(ledger: Ledger, report: ArticleReport) -> None:
    article = report.article
    titles = {c.criterion_id: c for c in ledger.criteria}
    print(
        f"{article.content_id}  {article.page.title_ja}  [{article.kind}] {article.path.as_posix()}"
    )
    review = report.review
    if review:
        changed = review["body_sha256"] != article.body_hash
        print(
            f"レビュー: {review['reviewed_on']} by {review['reviewer']}"
            + ("（その後本文が変わった）" if changed else "")
        )
        if review.get("notes"):
            print(f"  メモ: {review['notes']}")
    else:
        print("レビュー: なし")
    print(
        f"状態: {report.status}  図の水準: {report.visual_level}  "
        f"学習経路: {'あり' if article.on_learning_path else 'なし'}  "
        f"文体警告: {report.style_warning_count}"
    )
    for result in report.results:
        criterion = titles[result.criterion_id]
        detail = f"  — {result.detail}" if result.detail else ""
        print(
            f"  {MARK[result.state]} {result.state:<10} {result.criterion_id:<28} "
            f"{criterion.title_ja}{detail}"
        )


def next_queue(reports: tuple[ArticleReport, ...], limit: int, as_json: bool) -> None:
    queue = [report for report in sorted(reports, key=priority) if report.status != "達成"][:limit]
    if as_json:
        print(json.dumps([_report_json(report) for report in queue], ensure_ascii=False, indent=2))
        return
    for report in queue:
        todo = [r for r in report.results if r.state in ("fail", "stale", "new")]
        unreviewed = report.count("unreviewed")
        print(f"{report.article.content_id} [{report.article.kind}] {report.status}")
        for result in todo:
            detail = f" — {result.detail}" if result.detail else ""
            print(f"    {result.state:<10} {result.criterion_id}{detail}")
        if unreviewed:
            print(f"    unreviewed {unreviewed}基準（show で一覧）")


def record(args: argparse.Namespace, ledger: Ledger, reports: tuple[ArticleReport, ...]) -> None:
    report = _find(reports, args.content_id)
    applicable = [c.criterion_id for c in review_criteria_for(report.article, ledger)]
    verdicts: dict[str, Any] = {}
    for item in args.fail:
        criterion_id, _, note = item.partition("=")
        verdicts[criterion_id] = {"verdict": "fail", "note": note} if note else "fail"
    for name, given in (("na", args.na), ("pass", args.passed)):
        for criterion_id in (x for group in given for x in group.split(",") if x):
            if criterion_id == "all":
                for item in applicable:
                    verdicts.setdefault(item, name)
            else:
                verdicts.setdefault(criterion_id, name)
    missing = [item for item in applicable if item not in verdicts]
    if missing:
        raise SystemExit("verdict missing for: " + ", ".join(missing) + " (use --pass all)")
    entry = record_review(
        ROOT,
        report.article.content_id,
        reviewer=args.reviewer,
        reviewed_on=args.date,
        verdicts=verdicts,
        waivers=dict(item.partition("=")[::2] for item in args.waive),
        notes=args.note,
    )
    print(json.dumps({report.article.content_id: entry}, ensure_ascii=False, indent=2))


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    commands = parser.add_subparsers(dest="command")
    show_parser = commands.add_parser("show", help="one or more articles' checklists")
    show_parser.add_argument("ids", nargs="+", help="content ID, file stem, or path")
    next_parser = commands.add_parser("next", help="articles to fix or review next")
    next_parser.add_argument("--limit", type=int, default=10)
    commands.add_parser("criteria", help="list the criteria")
    record_parser = commands.add_parser("record", help="record a review of the current body")
    record_parser.add_argument("content_id")
    record_parser.add_argument(
        "--reviewer", required=True, choices=("owner", "claude", "codex", "human")
    )
    record_parser.add_argument("--date", default=date.today().isoformat())
    record_parser.add_argument(
        "--pass", dest="passed", action="append", default=[], help="IDs or all"
    )
    record_parser.add_argument("--fail", action="append", default=[], help="ID or ID=note")
    record_parser.add_argument("--na", action="append", default=[], help="comma-separated IDs")
    record_parser.add_argument(
        "--waive", action="append", default=[], help="AUTO_ID=reason (heuristic misfires)"
    )
    record_parser.add_argument("--note", default="")
    args = parser.parse_args()

    ledger, reports = evaluate_all(ROOT)
    if args.command == "record":
        record(args, ledger, reports)
    elif args.command == "criteria":
        for criterion in ledger.criteria:
            scope = " (学習経路のみ)" if criterion.scope == "learning_path" else ""
            print(
                f"{criterion.check:<6} {criterion.criterion_id:<28} {criterion.title_ja}{scope}\n"
                f"       対象: {', '.join(criterion.applies_to)}  since {criterion.since}  "
                f"根拠: {criterion.guide}"
            )
    elif args.command == "next":
        next_queue(reports, args.limit, args.json)
    elif args.command == "show":
        selected = [_find(reports, key) for key in args.ids]
        if args.json:
            print(json.dumps([_report_json(r) for r in selected], ensure_ascii=False, indent=2))
        else:
            for report in selected:
                show(ledger, report)
                print()
    elif args.json:
        print(json.dumps([_report_json(r) for r in reports], ensure_ascii=False, indent=2))
    else:
        summary(ledger, reports)


if __name__ == "__main__":
    main()
