from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from optimization_compass.article_quality import (
    AUTO_CHECKS,
    CRITERIA_PATH,
    LEDGER_PATH,
    broken_display_math,
    evaluate_all,
    ledger_problems,
    load_articles,
    load_ledger,
    record_review,
    require_ledger_integrity,
)

ROOT = Path(__file__).parents[1]
REFERENCE = "concept.linear-least-squares"


def _copy_repo_subset(tmp_path: Path) -> Path:
    """The two ledgered articles the tests touch, with the inputs and figures they need."""
    for relative in (
        Path("content/concepts/linear-least-squares.md"),
        Path("content/methods/adam.md"),
        Path("site/public/figures"),
        CRITERIA_PATH,
        Path("data/seeds/learning_paths.json"),
    ):
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy(source, target)
    ledger = json.loads((ROOT / LEDGER_PATH).read_text(encoding="utf-8"))
    ledger["reviews"] = {
        key: value for key, value in ledger["reviews"].items() if key in (REFERENCE, "adam")
    }
    (tmp_path / LEDGER_PATH).write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_committed_ledger_is_well_formed() -> None:
    require_ledger_integrity(ROOT)


def test_every_auto_criterion_has_a_probe_and_every_probe_a_criterion() -> None:
    ledger = load_ledger(ROOT)
    auto = {c.criterion_id for c in ledger.criteria if c.check == "auto"}
    assert auto == set(AUTO_CHECKS)


def test_reference_article_meets_every_criterion() -> None:
    """The owner-accepted reference defines the bar; a probe that fails it is miscalibrated."""
    _, reports = evaluate_all(ROOT)
    report = next(r for r in reports if r.article.content_id == REFERENCE)
    assert report.status == "達成", [(r.criterion_id, r.state, r.detail) for r in report.results]


def test_edit_after_review_marks_review_criteria_stale(tmp_path: Path) -> None:
    root = _copy_repo_subset(tmp_path)
    article = next(a for a in load_articles(root) if a.content_id == REFERENCE)
    path = root / article.path
    path.write_text(path.read_text(encoding="utf-8") + "\n追記した段落です。\n", encoding="utf-8")

    _, reports = evaluate_all(root)
    report = next(r for r in reports if r.article.content_id == REFERENCE)
    review_states = {r.state for r in report.results if r.criterion_id == "example.computed"}
    assert review_states == {"stale"}
    assert report.status == "要レビュー"


def test_criterion_tightened_after_review_is_new(tmp_path: Path) -> None:
    root = _copy_repo_subset(tmp_path)
    criteria_path = root / CRITERIA_PATH
    raw = json.loads(criteria_path.read_text(encoding="utf-8"))
    for item in raw["criteria"]:
        if item["criterion_id"] == "pitfalls.with-example":
            item["since"] = "2999-01-01"
    criteria_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    _, reports = evaluate_all(root)
    report = next(r for r in reports if r.article.content_id == REFERENCE)
    states = {r.criterion_id: r.state for r in report.results}
    assert states["pitfalls.with-example"] == "new"
    assert states["example.computed"] == "pass"


def test_unreviewed_article_lists_every_review_criterion() -> None:
    ledger, reports = evaluate_all(ROOT)
    report = next(r for r in reports if r.review is None and r.article.kind == "method")
    review_ids = {c.criterion_id for c in ledger.criteria if c.check == "review"}
    unreviewed = {r.criterion_id for r in report.results if r.state == "unreviewed"}
    assert unreviewed and unreviewed <= review_ids


def test_record_review_pins_current_body_and_rejects_auto_verdicts(tmp_path: Path) -> None:
    root = _copy_repo_subset(tmp_path)
    entry = record_review(
        root,
        "adam",
        reviewer="claude",
        reviewed_on="2026-10-04",
        verdicts={"example.computed": {"verdict": "fail", "note": "表の3歩目が手計算と合わない"}},
    )
    assert len(entry["body_sha256"]) == 12
    _, reports = evaluate_all(root)
    report = next(r for r in reports if r.article.content_id == "adam")
    failed = {r.criterion_id: r.detail for r in report.results if r.state == "fail"}
    assert failed["example.computed"] == "表の3歩目が手計算と合わない"

    with pytest.raises(ValueError, match="measured automatically"):
        record_review(
            root, "adam", reviewer="claude", reviewed_on="2026-10-04", verdicts={"skeleton": "pass"}
        )


def test_ledger_rejects_unknown_articles_and_reasonless_waivers() -> None:
    ledger = load_ledger(ROOT)
    ledger.reviews["no-such-article"] = {}
    ledger.reviews["adam"] = {
        "reviewed_on": "2026-10-04",
        "reviewer": "claude",
        "body_sha256": "0" * 12,
        "verdicts": {},
        "waivers": {"figure.checks-after": " "},
    }
    problems = ledger_problems(ledger, load_articles(ROOT))
    assert any("no-such-article" in item for item in problems)
    assert any("needs a reason" in item for item in problems)


def test_math_probe_flags_rows_that_the_site_converter_drops() -> None:
    """latex2mathml keeps pmatrix and cases rows but flattens aligned, showing ``&`` as text."""
    aligned = "$$\n\\begin{aligned}\na&=1\\\\\nb&=2\n\\end{aligned}\n$$"
    pmatrix = "$$\nA=\\begin{pmatrix}4&6\\\\6&14\\end{pmatrix}\n$$"
    cases = "$$\nf=\\begin{cases}1 & x>0\\\\ 0 & x\\le0\\end{cases}\n$$"
    assert len(broken_display_math(aligned)) == 1
    assert broken_display_math(f"{pmatrix}\n\n{cases}") == []
