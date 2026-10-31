"""Article quality ledger: which published article meets which teaching criterion, and since when.

Two committed inputs drive it (docs/article-quality.md):

- ``data/seeds/article_quality_criteria.json`` lists every criterion. ``check: auto`` criteria are
  measured from the Markdown on every run; ``check: review`` criteria need a reader (the owner or
  an agent) and are recorded in the ledger. ``since`` is the date a criterion was added or last
  tightened, so reviews made before that date no longer cover it.
- ``data/seeds/article_quality_ledger.json`` records each review: date, reviewer, the hash of the
  article body that was reviewed, and one verdict per review criterion.

From those two files and the articles, the ledger reports what is missing: articles never reviewed,
articles edited after their review, criteria added after the review, and auto checks that fail.
Nothing here fails a build except a malformed ledger (``require_ledger_integrity``); quality gaps
are a work queue, not a gate.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast

from latex2mathml.converter import convert as latex_to_mathml

from optimization_compass.content_models import ContentPage, parse_content
from optimization_compass.content_quality import language_contract_warnings, style_warnings
from optimization_compass.content_skeletons import skeleton_gaps, skeleton_kind

CRITERIA_PATH = Path("data/seeds/article_quality_criteria.json")
LEDGER_PATH = Path("data/seeds/article_quality_ledger.json")
CONTRACT_VERSION = "1.0.0"

ArticleKind = Literal["formulation", "method", "family", "concept"]
ARTICLE_KINDS: tuple[ArticleKind, ...] = ("formulation", "method", "family", "concept")
Verdict = Literal["pass", "fail", "na"]
VERDICTS: tuple[Verdict, ...] = ("pass", "fail", "na")
# What a reader of the report sees for one criterion of one article.
State = Literal["pass", "fail", "na", "waived", "unreviewed", "stale", "new"]
REVIEWERS = ("owner", "claude", "codex", "human")

_EXPLORABLE_OPEN = re.compile(r"^::: explorable (\S+)", re.MULTILINE)
_IMAGE = re.compile(r"^!\[", re.MULTILINE)
_SCENE = re.compile(r"\(#/theater/")
_SVG_REF = re.compile(r"\]\(\./((?:figures|media)/[^)\s]+\.svg)")
_FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
_DISPLAY_MATH = re.compile(r"\$\$.*?\$\$", re.DOTALL)
_DISPLAY_MATH_BODY = re.compile(r"^\$\$\s*\n(.*?)\n\$\$", re.MULTILINE | re.DOTALL)
_NUMBERED = re.compile(r"^\d+\. ")
_UI_NAME = re.compile(r"「[^」]+」")
_ACTION_VERB = re.compile(r"動か|押|選|クリック|ドラッグ|切り替|進め|開|上げ|下げ|掘|触")
_DIRECTION = re.compile(r"[左右上下](?:側)?の(?:図|パネル|グラフ)|図の[左右](?:側)?")
_EXAMPLE_COLUMN = re.compile(r"^\|.*例では.*\|\s*\n\|[\s:|-]+\|", re.MULTILINE)
_VIEWBOX_WIDTH = re.compile(r'viewBox="[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)')
_FONT_SIZE = re.compile(r'font-size(?:="|:\s*)([\d.]+)|font:[^;"]*?([\d.]+)px')
PHONE_WIDTH = 353.0
PC_WIDTH = {"figures": 440.0, "media": 672.0}
# Where the main explorable must already have appeared (playbook §5.3).
_MAIN_FIGURE_BEFORE = {"formulation": "標準形を読む", "method": "向く条件・避ける条件"}


@dataclass(frozen=True)
class Criterion:
    criterion_id: str
    title_ja: str
    check: Literal["auto", "review"]
    applies_to: tuple[ArticleKind, ...]
    since: str
    guide: str
    scope: Literal["all", "learning_path"] = "all"


@dataclass(frozen=True)
class Article:
    page: ContentPage
    path: Path
    kind: ArticleKind
    on_learning_path: bool

    @property
    def content_id(self) -> str:
        return self.page.content_id

    @property
    def body_hash(self) -> str:
        return body_hash(self.page.body)


@dataclass(frozen=True)
class CheckResult:
    criterion_id: str
    state: State
    detail: str = ""


@dataclass(frozen=True)
class ArticleReport:
    article: Article
    results: tuple[CheckResult, ...]
    review: Mapping[str, Any] | None
    style_warning_count: int
    visual_level: str

    def count(self, *states: State) -> int:
        return sum(result.state in states for result in self.results)

    @property
    def status(self) -> str:
        """``要修正`` on a failure, ``要レビュー`` on a missing/stale review, else ``達成``."""
        if self.count("fail"):
            return "要修正"
        if self.count("unreviewed", "stale", "new"):
            return "要レビュー"
        return "達成"

    @property
    def reviewer(self) -> str:
        return str(self.review["reviewer"]) if self.review else "-"


@dataclass
class Ledger:
    criteria: tuple[Criterion, ...]
    reviews: dict[str, dict[str, Any]] = field(default_factory=dict)


def body_hash(body: str) -> str:
    """Short hash of the article body, insensitive to line endings and trailing space."""
    normalized = "\n".join(line.rstrip() for line in body.replace("\r\n", "\n").splitlines())
    return hashlib.sha256(normalized.strip().encode("utf-8")).hexdigest()[:12]


def article_kind(page: ContentPage) -> ArticleKind:
    return skeleton_kind(page) or "concept"


def load_criteria(root: Path) -> tuple[Criterion, ...]:
    raw = json.loads((root / CRITERIA_PATH).read_text(encoding="utf-8"))
    if raw.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"{CRITERIA_PATH} must be contract {CONTRACT_VERSION}")
    criteria = []
    for item in raw["criteria"]:
        applies = tuple(item["applies_to"])
        if not applies or any(kind not in ARTICLE_KINDS for kind in applies):
            raise ValueError(f"{item['criterion_id']} applies_to must name {ARTICLE_KINDS}")
        if item["check"] == "auto" and item["criterion_id"] not in AUTO_CHECKS:
            raise ValueError(f"{item['criterion_id']} is auto but has no probe")
        criteria.append(
            Criterion(
                criterion_id=item["criterion_id"],
                title_ja=item["title_ja"],
                check=item["check"],
                applies_to=applies,
                since=item["since"],
                guide=item["guide"],
                scope=item.get("scope", "all"),
            )
        )
    ids = [criterion.criterion_id for criterion in criteria]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{CRITERIA_PATH} lists a criterion twice")
    return tuple(criteria)


def load_ledger(root: Path) -> Ledger:
    criteria = load_criteria(root)
    raw = json.loads((root / LEDGER_PATH).read_text(encoding="utf-8"))
    if raw.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"{LEDGER_PATH} must be contract {CONTRACT_VERSION}")
    return Ledger(criteria=criteria, reviews=dict(raw["reviews"]))


def save_ledger(root: Path, ledger: Ledger) -> None:
    payload = {
        "contract_version": CONTRACT_VERSION,
        "reviews": {key: ledger.reviews[key] for key in sorted(ledger.reviews)},
    }
    (root / LEDGER_PATH).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


def learning_path_targets(root: Path) -> frozenset[str]:
    """Content IDs and formulation IDs (``PAxxx``) that some learning path steps through."""
    raw = json.loads((root / "data/seeds/learning_paths.json").read_text(encoding="utf-8"))
    return frozenset(step["target_id"] for path in raw["paths"] for step in path["steps"])


def load_articles(root: Path) -> tuple[Article, ...]:
    targets = learning_path_targets(root)
    articles = []
    for path in sorted((root / "content").rglob("*.md")):
        page = parse_content(path)
        if page.status != "published":
            continue
        kind = article_kind(page)
        on_path = page.content_id in targets or (
            kind == "formulation" and page.canonical_entity_id in targets
        )
        articles.append(Article(page, path.relative_to(root), kind, on_path))
    return tuple(articles)


def applies(criterion: Criterion, article: Article) -> bool:
    if article.kind not in criterion.applies_to:
        return False
    return criterion.scope == "all" or article.on_learning_path


# --- auto probes -------------------------------------------------------------------------------
# Each probe returns (verdict, detail). They measure the Markdown; they cannot judge teaching.

Probe = Callable[[Article, Path], tuple[Verdict, str]]


def _prose(body: str) -> str:
    return _DISPLAY_MATH.sub("", _FENCE.sub("", body))


def _explorables(body: str) -> list[re.Match[str]]:
    return list(_EXPLORABLE_OPEN.finditer(body))


def visual_level(page: ContentPage) -> str:
    if _EXPLORABLE_OPEN.search(page.body):
        return "explorable"
    if _SCENE.search(page.body) or page.visualization_ids:
        return "scene"
    if _IMAGE.search(page.body):
        return "static"
    return "none"


def svg_text_sizes(svg: str, folder: str) -> tuple[float, float, float, float] | None:
    """Smallest/largest displayed text size on a PC and on a phone, or None if unmeasurable."""
    width_match = _VIEWBOX_WIDTH.search(svg)
    sizes = [float(a or b) for a, b in _FONT_SIZE.findall(svg)]
    if width_match is None or not sizes:
        return None
    width = float(width_match.group(1))
    pc = min(width, PC_WIDTH[folder]) / width
    phone = min(width, PHONE_WIDTH) / width
    return min(sizes) * pc, max(sizes) * pc, min(sizes) * phone, max(sizes) * phone


def svg_text_ok(sizes: tuple[float, float, float, float] | None) -> bool:
    return sizes is not None and sizes[2] >= 12 and sizes[1] <= 18


def _skeleton(article: Article, root: Path) -> tuple[Verdict, str]:
    gaps = skeleton_gaps(article.page)
    return ("fail", ", ".join(gaps)) if gaps else ("pass", "")


def _figure(article: Article, root: Path) -> tuple[Verdict, str]:
    level = visual_level(article.page)
    return ("fail", "図が一枚もない") if level == "none" else ("pass", level)


def _interactive(article: Article, root: Path) -> tuple[Verdict, str]:
    level = visual_level(article.page)
    return ("pass", "") if level == "explorable" else ("fail", f"いまは {level}")


def _main_figure_early(article: Article, root: Path) -> tuple[Verdict, str]:
    found = _explorables(article.page.body)
    anchor = _MAIN_FIGURE_BEFORE.get(article.kind)
    if not found or anchor is None:
        return "na", "操作図なし"
    heading = re.search(rf"^## {re.escape(anchor)}\s*$", article.page.body, re.MULTILINE)
    if heading is None or found[0].start() < heading.start():
        return "pass", ""
    return "fail", f"主図が「{anchor}」より後"


def _figure_lead(article: Article, root: Path) -> tuple[Verdict, str]:
    body = article.page.body
    found = _explorables(body)
    if not found:
        return "na", "操作図なし"
    before = [line for line in body[: found[0].start()].splitlines() if line.strip()][-3:]
    lead = "\n".join(before)
    if _ACTION_VERB.search(lead) and (_UI_NAME.search(lead) or "ください" in lead):
        return "pass", ""
    return "fail", "直前の3行に、操作の指示（「UI名」か「〜してください」）がない"


def _figure_followup(article: Article, root: Path) -> tuple[Verdict, str]:
    body = article.page.body
    found = _explorables(body)
    if not found:
        return "na", "操作図なし"
    lines = body[found[0].end() :].splitlines()
    closing = next((i for i, line in enumerate(lines) if line.strip() == ":::"), len(lines))
    numbered = 0
    for line in lines[closing + 1 :]:
        if line.startswith(("## ", "::: ")):
            break
        numbered += bool(_NUMBERED.match(line.strip()))
    if numbered >= 3:
        return "pass", ""
    return "fail", f"図の後の番号付きの確かめ項目が{numbered}個"


def _symbol_table(article: Article, root: Path) -> tuple[Verdict, str]:
    if _EXAMPLE_COLUMN.search(article.page.body):
        return "pass", ""
    return "fail", "見出しに「例では」を含む表がない"


def _code_output(article: Article, root: Path) -> tuple[Verdict, str]:
    body = article.page.body
    blocks = [match for match in _FENCE.finditer(body) if match.group(1) == "python"]
    if not blocks:
        return ("fail", "Pythonコードがない") if article.kind == "method" else ("na", "コードなし")
    printed = missing = 0
    for match in blocks:
        after = next((line for line in body[match.end() :].splitlines() if line.strip()), "")
        if after.startswith(("|", "```")):
            continue  # the output is shown as a table or a text block right after the code
        lines = match.group(2).splitlines()
        for index, line in enumerate(lines):
            if "print(" not in line:
                continue
            printed += 1
            following = next((x.strip() for x in lines[index + 1 :] if x.strip()), "")
            missing += "#" not in line and not following.startswith("#")
    if missing:
        return "fail", f"出力コメントのないprintが{missing}行"
    if not printed and not any(
        next((x for x in body[m.end() :].splitlines() if x.strip()), "").startswith(("|", "```"))
        for m in blocks
    ):
        return "fail", "printも出力の表もない"
    return "pass", ""


def _no_progress_report(article: Article, root: Path) -> tuple[Verdict, str]:
    codes = ("prose.meta", "prose.work-report")
    hits = [w for w in style_warnings(article.page) if w.code in codes]
    if hits:
        return "fail", "; ".join(f"line~{w.line} {w.detail}" for w in hits[:3])
    return "pass", ""


def _no_direction_words(article: Article, root: Path) -> tuple[Verdict, str]:
    hits = sorted(set(_DIRECTION.findall(_prose(article.page.body))))
    return ("fail", "、".join(hits)) if hits else ("pass", "")


def _no_language_mixing(article: Article, root: Path) -> tuple[Verdict, str]:
    hits = language_contract_warnings(article.page)
    if hits:
        return "fail", "; ".join(f"line~{w.line} {w.detail}" for w in hits[:3])
    return "pass", ""


def _figure_text(article: Article, root: Path) -> tuple[Verdict, str]:
    refs = sorted(set(_SVG_REF.findall(article.page.body)))
    if not refs:
        return "na", "静止SVGなし"
    bad = []
    for ref in refs:
        svg_path = root / "site" / "public" / ref
        if not svg_path.exists():
            bad.append(f"{ref}（ファイルなし）")
            continue
        sizes = svg_text_sizes(svg_path.read_text(encoding="utf-8"), ref.split("/")[0])
        if not svg_text_ok(sizes):
            bad.append(ref)
    return ("fail", ", ".join(bad)) if bad else ("pass", f"{len(refs)}枚")


def broken_display_math(body: str) -> list[str]:
    """Row breaks or ``&`` must become MathML table rows; otherwise the reader sees them as text."""
    broken = []
    for tex in _DISPLAY_MATH_BODY.findall(body.replace("\r\n", "\n")):
        if ("\\\\" in tex or "&" in tex) and "<mtr" not in latex_to_mathml(tex, display="block"):
            broken.append(" ".join(tex.split())[:40])
    return broken


def _math_renders(article: Article, root: Path) -> tuple[Verdict, str]:
    broken = broken_display_math(article.page.body)
    if broken:
        return "fail", "崩れる数式: " + " / ".join(broken)
    return "pass", ""


def _sources(article: Article, root: Path) -> tuple[Verdict, str]:
    return ("pass", "") if article.page.source_ids else ("fail", "source_idsが空")


AUTO_CHECKS: dict[str, Probe] = {
    "skeleton": _skeleton,
    "visual.figure": _figure,
    "visual.interactive": _interactive,
    "figure.main-early": _main_figure_early,
    "figure.first-action": _figure_lead,
    "figure.checks-after": _figure_followup,
    "reading.example-column": _symbol_table,
    "code.output-comments": _code_output,
    "prose.no-progress-report": _no_progress_report,
    "prose.no-direction-words": _no_direction_words,
    "prose.no-language-mixing": _no_language_mixing,
    "figure.text-size": _figure_text,
    "math.renders": _math_renders,
    "evidence.sources": _sources,
}


# --- evaluation --------------------------------------------------------------------------------


def _verdict_of(entry: object) -> tuple[str, str]:
    if isinstance(entry, str):
        return entry, ""
    if isinstance(entry, dict):
        return str(entry.get("verdict")), str(entry.get("note", ""))
    return "", ""


def evaluate(article: Article, ledger: Ledger, root: Path) -> ArticleReport:
    review = ledger.reviews.get(article.content_id)
    changed = review is not None and review.get("body_sha256") != article.body_hash
    results = []
    for criterion in ledger.criteria:
        if not applies(criterion, article):
            continue
        if criterion.check == "auto":
            verdict, detail = AUTO_CHECKS[criterion.criterion_id](article, root)
            waiver = (review or {}).get("waivers", {}).get(criterion.criterion_id)
            if verdict == "fail" and waiver:
                results.append(CheckResult(criterion.criterion_id, "waived", str(waiver)))
            else:
                results.append(CheckResult(criterion.criterion_id, verdict, detail))
            continue
        if review is None:
            results.append(CheckResult(criterion.criterion_id, "unreviewed"))
            continue
        entry = review.get("verdicts", {}).get(criterion.criterion_id)
        recorded, note = _verdict_of(entry)
        if entry is None or str(review["reviewed_on"]) < criterion.since:
            results.append(CheckResult(criterion.criterion_id, "new", f"基準 {criterion.since}"))
        elif changed and recorded != "na":
            # An edit can break a passing criterion or fix a failing one; either way re-read it.
            results.append(CheckResult(criterion.criterion_id, "stale", f"前回 {recorded}"))
        else:
            results.append(CheckResult(criterion.criterion_id, cast(State, recorded), note))
    return ArticleReport(
        article=article,
        results=tuple(results),
        review=review,
        style_warning_count=len(style_warnings(article.page)),
        visual_level=visual_level(article.page),
    )


def evaluate_all(root: Path) -> tuple[Ledger, tuple[ArticleReport, ...]]:
    ledger = load_ledger(root)
    reports = tuple(evaluate(article, ledger, root) for article in load_articles(root))
    return ledger, reports


def ledger_problems(ledger: Ledger, articles: Iterable[Article]) -> tuple[str, ...]:
    """Structural errors only: unknown articles/criteria, bad verdicts, dates, or hashes."""
    known = {article.content_id: article for article in articles}
    criteria = {criterion.criterion_id: criterion for criterion in ledger.criteria}
    problems = []
    for content_id, review in ledger.reviews.items():
        if content_id not in known:
            problems.append(f"{content_id}: not a published article")
            continue
        if review.get("reviewer") not in REVIEWERS:
            problems.append(f"{content_id}: reviewer must be one of {REVIEWERS}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(review.get("reviewed_on", ""))):
            problems.append(f"{content_id}: reviewed_on must be YYYY-MM-DD")
        if not re.fullmatch(r"[0-9a-f]{12}", str(review.get("body_sha256", ""))):
            problems.append(f"{content_id}: body_sha256 must be 12 hex characters")
        for criterion_id, entry in dict(review.get("verdicts", {})).items():
            criterion = criteria.get(criterion_id)
            if criterion is None:
                problems.append(f"{content_id}: unknown criterion {criterion_id}")
            elif criterion.check != "review":
                problems.append(f"{content_id}: {criterion_id} is measured automatically")
            elif not applies(criterion, known[content_id]):
                problems.append(f"{content_id}: {criterion_id} does not apply to this article")
            if _verdict_of(entry)[0] not in VERDICTS:
                problems.append(f"{content_id}: {criterion_id} verdict must be {VERDICTS}")
        for criterion_id, reason in dict(review.get("waivers", {})).items():
            criterion = criteria.get(criterion_id)
            if criterion is None or criterion.check != "auto":
                problems.append(f"{content_id}: waiver must name an auto criterion: {criterion_id}")
            if not isinstance(reason, str) or not reason.strip():
                problems.append(f"{content_id}: waiver {criterion_id} needs a reason")
    return tuple(problems)


def require_ledger_integrity(root: Path) -> None:
    problems = ledger_problems(load_ledger(root), load_articles(root))
    if problems:
        raise ValueError("article quality ledger is malformed: " + "; ".join(problems))


def record_review(
    root: Path,
    content_id: str,
    *,
    reviewer: str,
    reviewed_on: str,
    verdicts: Mapping[str, Verdict | dict[str, str]],
    waivers: Mapping[str, str] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Write one review for the current article body, replacing any earlier one."""
    ledger = load_ledger(root)
    articles = load_articles(root)
    article = next((a for a in articles if a.content_id == content_id), None)
    if article is None:
        raise ValueError(f"{content_id} is not a published article")
    entry: dict[str, Any] = {
        "reviewed_on": reviewed_on,
        "reviewer": reviewer,
        "body_sha256": article.body_hash,
        "verdicts": {key: verdicts[key] for key in sorted(verdicts)},
    }
    if waivers:
        entry["waivers"] = {key: waivers[key] for key in sorted(waivers)}
    if notes:
        entry["notes"] = notes
    ledger.reviews[content_id] = entry
    problems = ledger_problems(ledger, articles)
    if problems:
        raise ValueError("; ".join(problems))
    save_ledger(root, ledger)
    return entry


def review_criteria_for(article: Article, ledger: Ledger) -> tuple[Criterion, ...]:
    return tuple(c for c in ledger.criteria if c.check == "review" and applies(c, article))


def priority(report: ArticleReport) -> tuple[int, int, int, str]:
    """Learning-path articles first, then formulation/method, then the most failing checks."""
    article = report.article
    return (
        0 if article.on_learning_path else 1,
        0 if article.kind in ("formulation", "method") else 1,
        -(report.count("fail") * 2 + report.count("stale", "new", "unreviewed")),
        article.content_id,
    )
