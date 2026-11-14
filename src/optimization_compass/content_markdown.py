from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

from latex2mathml.converter import convert as latex_to_mathml
from markdown_it import MarkdownIt
from markdown_it.token import Token
from mdit_py_plugins.container import container_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from optimization_compass.explorables import (
    Explorable,
    Param,
    is_valid_explorable_id,
    load_explorables,
)

_EXPLORABLE_OPEN = "container_explorable_open"
_EXPLORABLE_CLOSE = "container_explorable_close"
_LESSON_OPEN = "container_lesson_open"
_LESSON_CLOSE = "container_lesson_close"
_STEP_OPEN = "container_step_open"
_STEP_CLOSE = "container_step_close"
_STEP_DEFAULT_SECONDS = 6.0
_LESSON_MAX_SECONDS = 120.0
_NUMBER = r"-?\d+(?:\.\d+)?"
_STEP_SWEEP = re.compile(rf"^({_NUMBER})\.\.({_NUMBER})(?:@({_NUMBER}))?$")
_STEP_NUMBER = re.compile(rf"^{_NUMBER}$")
_EXPLORABLE_FALLBACK = (
    "動かして確かめる図です。JavaScriptが有効なブラウザで表示されます。"
    "読み込めない場合は、下の説明で内容を確認してください。"
)
_ALLOWED_CODE_LANGUAGES = {"bash", "json", "python", "text", "yaml"}
_CALLOUTS = {"note": "Note", "tip": "Tip", "warning": "Warning"}
_HEADING_ID_PATTERN = re.compile(r"[^a-z0-9\u3040-\u30ff\u3400-\u9fff]+")


@dataclass(frozen=True)
class ContentHeading:
    heading_id: str
    label: str
    level: int


@dataclass(frozen=True)
class RenderedMarkdown:
    html: str
    toc: tuple[ContentHeading, ...]
    summary: str


def render_markdown(source: str, *, path: Path) -> RenderedMarkdown:
    if not source.strip():
        raise ValueError(f"{path}: content body must not be blank")
    _validate_fences(source, path)
    _reject_dangerous_authored_urls(source, path)
    parser = _markdown_parser()
    tokens = parser.parse(source)
    _reject_raw_html(tokens, path)
    headings = _prepare_headings(tokens, path)
    _validate_explorables(tokens, path, _prepare_lessons(tokens, path))
    _validate_figures_are_standalone(tokens, path)
    _validate_and_prepare_links(tokens, headings, path)
    _validate_code_languages(tokens, path)
    summary = _first_paragraph(tokens, path)
    return RenderedMarkdown(
        html=parser.renderer.render(tokens, parser.options, {}).strip(),
        toc=tuple(headings),
        summary=summary,
    )


def unrenderable_math(source: str) -> tuple[str, ...]:
    """Formulas whose row breaks or alignment the site's LaTeX to MathML conversion would garble.

    latex2mathml turns ``\\\\`` and ``&`` into table rows and cells only inside environments it
    knows (``cases``, ``array``, ``pmatrix``...). Elsewhere, ``aligned`` included, it emits
    ``<mspace linebreak="newline"/>``, which browsers ignore, and a bare ``&`` that reads as a
    symbol, so the rows run together on one line. Returns the offending TeX, whitespace-collapsed.
    """
    broken = []
    for token in _walk(_markdown_parser().parse(source)):
        if not token.type.startswith("math"):
            continue
        display = "block" if token.type.startswith("math_block") else "inline"
        mathml = latex_to_mathml(token.content, display=display)
        if 'linebreak="newline"' in mathml or "<mi>&</mi>" in mathml:
            broken.append(" ".join(token.content.split()))
    return tuple(broken)


def render_inline_markdown(source: str) -> str:
    """Render trusted short metadata with the same math pipeline as articles."""
    if not source.strip():
        raise ValueError("inline Markdown source must not be blank")
    return str(_markdown_parser().renderInline(source).strip())


def _reject_dangerous_authored_urls(source: str, path: Path) -> None:
    match = re.search(
        r"!?\[[^\]]*\]\(\s*<?(?:javascript|data|vbscript|http):",
        source,
        flags=re.IGNORECASE,
    )
    if match:
        raise ValueError(
            f"{path}: URL must be an HTTPS URL, an absolute site path, or a local heading anchor"
        )


def _markdown_parser() -> MarkdownIt:
    parser = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    parser.enable("table")
    parser.use(dollarmath_plugin, allow_space=False, allow_digits=False)
    for name, label in _CALLOUTS.items():
        parser.use(container_plugin, name, render=_callout_renderer(name, label))
    parser.use(container_plugin, "explorable", render=_render_explorable)
    parser.use(container_plugin, "lesson", render=_render_lesson)
    parser.use(container_plugin, "step", render=_render_step)
    parser.add_render_rule("fence", _render_fence)
    parser.add_render_rule("code_block", _render_code_block)
    parser.add_render_rule("math_inline", _render_inline_math)
    parser.add_render_rule("math_block", _render_block_math)
    parser.add_render_rule("image", _render_image)
    parser.add_render_rule("paragraph_open", _render_paragraph_open)
    parser.add_render_rule("paragraph_close", _render_paragraph_close)
    return parser


def _callout_renderer(name: str, label: str) -> Any:
    def render(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
        if tokens[index].nesting == 1:
            return (
                f'<aside class="callout callout-{name}" role="note">'
                f'<p class="callout-label">{label}</p>\n'
            )
        return "</aside>\n"

    return render


def _render_explorable(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    token = tokens[index]
    if token.nesting == -1:
        return "</figcaption></figure>\n"
    explorable_id = token.info.split()[1]
    entry = load_explorables()[explorable_id]
    return (
        f'<figure class="explorable" role="group" data-explorable-id="{explorable_id}"'
        f' aria-label="{html.escape(entry.title_ja, quote=True)}">'
        f'<div class="explorable-mount" data-explorable-mount>'
        f'<p class="explorable-fallback">{_EXPLORABLE_FALLBACK}</p></div>'
        '<figcaption class="explorable-caption">'
    )


def _validate_explorables(tokens: list[Token], path: Path, in_lessons: set[str]) -> None:
    """An explorable is a top-level block: a registered id and exactly one caption paragraph."""
    registry = load_explorables()
    seen = set(in_lessons)
    for index, token in enumerate(tokens):
        if token.type != _EXPLORABLE_OPEN:
            continue
        parts = token.info.split()
        if len(parts) != 2 or not is_valid_explorable_id(parts[1]):
            raise ValueError(f"{path}: explorable requires exactly one kebab-case id")
        explorable_id = parts[1]
        if explorable_id not in registry:
            raise ValueError(f"{path}: unknown explorable id: {explorable_id}")
        if explorable_id in seen:
            raise ValueError(f"{path}: explorable is used more than once: {explorable_id}")
        seen.add(explorable_id)
        if token.level != 0:
            raise ValueError(f"{path}: explorable must be a top-level block: {explorable_id}")
        body = tokens[index + 1 : index + 4]
        closes = index + 4 < len(tokens) and tokens[index + 4].type == _EXPLORABLE_CLOSE
        if not (
            closes
            and [item.type for item in body] == ["paragraph_open", "inline", "paragraph_close"]
        ):
            raise ValueError(
                f"{path}: explorable {explorable_id} requires exactly one caption paragraph"
            )
        inline = body[1]
        if any(child.type == "image" for child in inline.children or []):
            raise ValueError(f"{path}: explorable caption must be text: {explorable_id}")
        if not _inline_text(inline).strip():
            raise ValueError(f"{path}: explorable caption must not be blank: {explorable_id}")


def _render_lesson(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    """Without JavaScript a lesson is the figure's fallback followed by its steps as a list."""
    token = tokens[index]
    if token.nesting == -1:
        return "</ol></section>\n"
    figure_id = token.info.split()[1]
    entry = load_explorables()[figure_id]
    return (
        f'<section class="lesson" data-lesson-figure="{figure_id}">'
        '<div class="lesson-stage">'
        f'<figure class="explorable lesson-figure" role="group" data-explorable-id="{figure_id}"'
        f' aria-label="{html.escape(entry.title_ja, quote=True)}">'
        '<div class="explorable-mount" data-explorable-mount>'
        f'<p class="explorable-fallback">{_EXPLORABLE_FALLBACK}</p></div></figure>'
        '<div class="lesson-nav" data-lesson-nav></div></div>'
        '<ol class="lesson-steps">\n'
    )


def _render_step(renderer: Any, tokens: list[Token], index: int, *_: object) -> str:
    token = tokens[index]
    if token.nesting == -1:
        return "</li>\n"
    return f'<li class="lesson-step" data-lesson-step{renderer.renderAttrs(token)}>\n'


def _prepare_lessons(tokens: list[Token], path: Path) -> set[str]:
    """Check every ``:::: lesson <figure-id>`` and write each step's data onto its token.

    Returns the figure ids the lessons use, so an explorable block cannot repeat one.
    """
    registry = load_explorables()
    used: set[str] = set()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type == _STEP_OPEN:
            raise ValueError(f"{path}: a step must be directly inside a lesson")
        if token.type != _LESSON_OPEN:
            index += 1
            continue
        parts = token.info.split()
        if len(parts) != 2 or not is_valid_explorable_id(parts[1]):
            raise ValueError(f"{path}: lesson requires exactly one kebab-case figure id")
        figure_id = parts[1]
        if figure_id not in registry:
            raise ValueError(f"{path}: unknown explorable id: {figure_id}")
        if figure_id in used:
            raise ValueError(f"{path}: explorable is used more than once: {figure_id}")
        used.add(figure_id)
        if token.level != 0:
            raise ValueError(f"{path}: lesson must be a top-level block: {figure_id}")
        entry = registry[figure_id]
        if entry.params is None:
            raise ValueError(
                f"{path}: lesson {figure_id}: the figure's meta.json must declare params"
            )
        where = f"{path}: lesson {figure_id}"
        end = _closing(tokens, index, _LESSON_OPEN, _LESSON_CLOSE)
        seconds: list[float] = []
        # What the figure shows when a step ends; a step that omits a param keeps it.
        carried: dict[str, float | str] = {
            name: param.default for name, param in entry.params.items() if param.default is not None
        }
        cursor = index + 1
        while cursor < end:
            if tokens[cursor].type != _STEP_OPEN:
                raise ValueError(f"{where}: only `::: step` blocks may appear inside a lesson")
            step_end = _closing(tokens, cursor, _STEP_OPEN, _STEP_CLOSE)
            step_where = f"{where} step {len(seconds) + 1}"
            seconds.append(_prepare_step(tokens, cursor, step_end, entry, carried, step_where))
            cursor = step_end + 1
        if not 2 <= len(seconds) <= 12:
            raise ValueError(f"{where}: a lesson has 2 to 12 steps, found {len(seconds)}")
        if sum(seconds) > _LESSON_MAX_SECONDS:
            raise ValueError(
                f"{where}: steps must not exceed {_LESSON_MAX_SECONDS:.0f} seconds in total"
            )
        index = end + 1
    return used


def _closing(tokens: list[Token], start: int, open_type: str, close_type: str) -> int:
    depth = 0
    for index in range(start, len(tokens)):
        if tokens[index].type == open_type:
            depth += 1
        elif tokens[index].type == close_type:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("container is not closed")  # markdown-it always emits the close token


def _prepare_step(
    tokens: list[Token],
    start: int,
    end: int,
    entry: Explorable,
    carried: dict[str, float | str],
    where: str,
) -> float:
    """Validate one step and set its data attributes. Returns its seconds.

    The step's settings are written out in full: a param it omits keeps the value the previous
    step ended on (``carried``, updated here), or the param's default in the first step.
    """
    token = tokens[start]
    params = entry.params or {}
    seconds = _STEP_DEFAULT_SECONDS
    predict = False
    answer: int | None = None
    settings: dict[str, object] = {}
    seen: set[str] = set()
    for word in token.info.split()[1:]:
        key, separator, value = word.partition("=")
        if key in seen:
            raise ValueError(f"{where}: key is given twice: {key}")
        seen.add(key)
        if key == "predict":
            if separator:
                raise ValueError(f"{where}: predict is a flag and takes no value")
            predict = True
        elif not value:
            raise ValueError(f"{where}: write keys as key=value: {word}")
        elif key == "seconds":
            if not _STEP_NUMBER.match(value) or not 2 <= float(value) <= 15:
                raise ValueError(f"{where}: seconds must be a number from 2 to 15")
            seconds = float(value)
        elif key == "answer":
            if not (value.isascii() and value.isdigit()):
                raise ValueError(f"{where}: answer must be the number of a choice, from 1")
            answer = int(value)
        elif key not in params:
            known = ", ".join(sorted(params)) or "none"
            raise ValueError(f"{where}: {key!r} is not a param of {entry.id} (its params: {known})")
        else:
            settings[key] = _step_value(key, value, params[key], where)

    body = tokens[start + 1 : end]
    level = token.level + 1
    for item in body:
        if item.type == "heading_open":
            raise ValueError(f"{where}: a step must not contain a heading")
        if item.type in {_LESSON_OPEN, _STEP_OPEN}:
            raise ValueError(f"{where}: a step must not contain another lesson or step")
    caption = next(
        (
            _first_sentence(_inline_text(body[position + 1]))
            for position, item in enumerate(body)
            if item.type == "paragraph_open" and item.level == level
        ),
        "",
    )
    if not caption:
        raise ValueError(
            f"{where}: a step needs a paragraph of text; its first sentence is the caption"
        )
    lists = [
        item
        for item in body
        if item.type in {"bullet_list_open", "ordered_list_open"} and item.level == level
    ]
    if predict:
        if len(lists) != 1:
            raise ValueError(f"{where}: a predict step has exactly one list, the choices")
        choices = sum(item.type == "list_item_open" and item.level == level + 1 for item in body)
        if not 2 <= choices <= 4:
            raise ValueError(f"{where}: a predict step offers 2 to 4 choices, found {choices}")
        if answer is None or not 1 <= answer <= choices:
            raise ValueError(f"{where}: a predict step needs answer=1..{choices}")
        lists[0].attrSet("class", "lesson-choices")
        lists[0].attrSet("data-lesson-choices", "")
        token.attrSet("data-predict", "")
        token.attrSet("data-answer", str(answer))
    elif answer is not None:
        raise ValueError(f"{where}: answer is only for a predict step")
    missing = sorted(set(params) - set(settings) - set(carried))
    if missing:
        raise ValueError(
            f"{where}: {', '.join(missing)} is not set and has no default in "
            f"{entry.id}/meta.json params"
        )
    full = {name: _plain_number(kept) for name, kept in carried.items()} | settings
    for name, setting in settings.items():
        carried[name] = _end_value(setting, seconds)
    token.attrSet("data-seconds", f"{seconds:g}")
    token.attrSet("data-settings", json.dumps(full, ensure_ascii=False, sort_keys=True))
    token.attrSet("data-caption", caption)
    return seconds


def _step_value(key: str, value: str, param: Param, where: str) -> object:
    """A constant, a sweep ``a..b`` or a rate ``a..b@r``, in the shape ``scene.ts`` reads."""
    sweep = _STEP_SWEEP.match(value)
    if sweep is None:
        if param.type == "choice":
            constant: float | str = value
        elif _STEP_NUMBER.match(value):
            constant = float(value)
        else:
            raise ValueError(f"{where}: {key}={value} must be a number, a..b or a..b@rate")
        problem = param.problem_with(constant)
        if problem:
            raise ValueError(f"{where}: {key}={value} {problem}")
        return _plain_number(constant)
    if param.type == "choice":
        raise ValueError(f"{where}: {key}={value}: only a number param can sweep")
    start, stop = float(sweep.group(1)), float(sweep.group(2))
    for endpoint in (start, stop):
        problem = param.problem_with(endpoint)
        if problem:
            raise ValueError(f"{where}: {key}={value}: {endpoint:g} {problem}")
    if start == stop:
        raise ValueError(f"{where}: {key}={value}: a sweep needs two different ends")
    moving: dict[str, object] = {"from": _plain_number(start), "to": _plain_number(stop)}
    if sweep.group(3) is not None:
        rate = float(sweep.group(3))
        if rate <= 0:
            raise ValueError(f"{where}: {key}={value}: the rate after @ must be positive")
        moving["rate"] = _plain_number(rate)
    if param.type == "integer":
        # The figure declared whole numbers, so the moving value advances in whole steps.
        moving["step"] = 1
    return moving


def _end_value(value: object, seconds: float) -> float | str:
    """Where a step leaves a param: the same arithmetic as ``resolveSettings`` in scene.ts."""
    if not isinstance(value, dict):
        return cast("float | str", value)
    start, stop = float(value["from"]), float(value["to"])
    if "rate" not in value:
        return stop
    travelled = min(abs(stop - start), float(value["rate"]) * seconds)
    if "step" in value:
        travelled = float(value["step"]) * (travelled // float(value["step"]))
    return start + travelled if stop > start else start - travelled


def _plain_number(value: float | str) -> float | int | str:
    if isinstance(value, str):
        return value
    return int(value) if float(value).is_integer() else value


def _first_sentence(text: str) -> str:
    text = " ".join(text.split())
    end = text.find("。")
    return text if end == -1 else text[: end + 1]


def _walk(tokens: list[Token]) -> list[Token]:
    result: list[Token] = []
    for token in tokens:
        result.append(token)
        if token.children:
            result.extend(_walk(token.children))
    return result


def _reject_raw_html(tokens: list[Token], path: Path) -> None:
    if any(token.type in {"html_block", "html_inline"} for token in _walk(tokens)):
        raise ValueError(f"{path}: raw HTML is forbidden in educational content")


def _prepare_headings(tokens: list[Token], path: Path) -> list[ContentHeading]:
    headings: list[ContentHeading] = []
    used_ids: set[str] = set()
    previous_level = 1
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        level = int(token.tag[1:])
        if level == 1:
            raise ValueError(f"{path}: body headings must start at level 2; page title owns h1")
        if level > previous_level + 1:
            raise ValueError(f"{path}: heading hierarchy skips from h{previous_level} to h{level}")
        inline = tokens[index + 1]
        label = _inline_text(inline).strip()
        if not label:
            raise ValueError(f"{path}: headings must contain text")
        base = _slug(label)
        heading_id = base
        suffix = 2
        while heading_id in used_ids:
            heading_id = f"{base}-{suffix}"
            suffix += 1
        used_ids.add(heading_id)
        token.attrSet("id", heading_id)
        token.attrSet("tabindex", "-1")
        headings.append(ContentHeading(heading_id=heading_id, label=label, level=level))
        previous_level = level
    if not headings:
        raise ValueError(f"{path}: content body must contain at least one level-2 heading")
    return headings


def _slug(label: str) -> str:
    slug = _HEADING_ID_PATTERN.sub("-", label.casefold()).strip("-")
    return slug or "section"


def _inline_text(token: Token) -> str:
    if not token.children:
        return token.content
    return "".join(
        child.content
        for child in token.children
        if child.type in {"text", "code_inline", "math_inline"}
    )


def _validate_figures_are_standalone(tokens: list[Token], path: Path) -> None:
    for token in tokens:
        if token.type != "inline" or not token.children:
            continue
        if any(child.type == "image" for child in token.children) and not _sole_image(token):
            raise ValueError(f"{path}: figures must be placed on their own line")


def _validate_and_prepare_links(
    tokens: list[Token], headings: list[ContentHeading], path: Path
) -> None:
    heading_ids = {heading.heading_id for heading in headings}
    for token in _walk(tokens):
        if token.type not in {"link_open", "image"}:
            continue
        attribute = "href" if token.type == "link_open" else "src"
        value = token.attrGet(attribute)
        if not isinstance(value, str):
            raise ValueError(f"{path}: {token.type} is missing {attribute}")
        kind = _classify_url(value, path)
        if kind == "anchor" and value[1:] not in heading_ids:
            raise ValueError(f"{path}: link targets unknown heading: {value}")
        if token.type == "link_open" and kind == "anchor":
            token.attrSet("data-heading-target", value[1:])
        if token.type == "link_open" and kind == "external":
            token.attrSet("target", "_blank")
            token.attrSet("rel", "noopener noreferrer")
        if token.type == "image":
            if kind == "asset":
                _validate_asset(value, path)
            alt = _inline_text(token).strip()
            raw_caption = token.attrGet("title")
            caption = raw_caption.strip() if isinstance(raw_caption, str) else ""
            if not alt or not caption:
                raise ValueError(f"{path}: figures require non-empty alt text and title caption")


def _classify_url(value: str, path: Path) -> str:
    if value.startswith("#/"):
        return "internal"
    if value.startswith("#") and len(value) > 1:
        return "anchor"
    if value.startswith("/") and not value.startswith("//"):
        return "internal"
    if value.startswith("./") and ".." not in value.split("/") and not urlsplit(value).query:
        return "asset"
    parsed = urlsplit(value)
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
        return "external"
    raise ValueError(
        f"{path}: URL must be an HTTPS URL, an absolute site path, or a local heading anchor: "
        f"{value}"
    )


def _validate_asset(value: str, path: Path) -> None:
    roots = [parent for parent in path.parents if parent.name == "content"]
    if not roots:
        raise ValueError(f"{path}: cannot resolve local asset outside content directory")
    public_asset = roots[0].parent / "site" / "public" / value.removeprefix("./")
    if not public_asset.is_file():
        raise ValueError(f"{path}: local asset does not exist: {value}")


def _validate_code_languages(tokens: list[Token], path: Path) -> None:
    for token in _walk(tokens):
        if token.type != "fence":
            continue
        language = token.info.strip().split(maxsplit=1)[0]
        if not language:
            raise ValueError(f"{path}: fenced code blocks require a language")
        if language not in _ALLOWED_CODE_LANGUAGES:
            raise ValueError(f"{path}: unsupported fenced code language: {language}")


def _validate_fences(source: str, path: Path) -> None:
    fence: tuple[str, int] | None = None
    for line in source.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if not match:
            continue
        marker = match.group(1)
        if fence is None:
            fence = (marker[0], len(marker))
        elif marker[0] == fence[0] and len(marker) >= fence[1] and not match.group(2).strip():
            fence = None
    if fence is not None:
        raise ValueError(f"{path}: fenced code block is not closed")


def _first_paragraph(tokens: list[Token], path: Path) -> str:
    for index, token in enumerate(tokens):
        if token.type == "paragraph_open" and index + 1 < len(tokens):
            inline = tokens[index + 1]
            if inline.type == "inline" and not _sole_image(inline):
                summary = _inline_text(inline).strip()
                if summary:
                    return summary
    raise ValueError(f"{path}: content body must contain a prose paragraph")


def _render_fence(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    token = tokens[index]
    language = token.info.strip().split(maxsplit=1)[0]
    try:
        lexer = get_lexer_by_name(language, stripall=False)
    except ClassNotFound as error:
        raise ValueError(f"unsupported fenced code language: {language}") from error
    highlighted = highlight(token.content, lexer, HtmlFormatter(nowrap=True)).rstrip("\n")
    label = html.escape(language)
    return (
        f'<div class="code-block"><span class="code-language">{label}</span>'
        f'<pre><code class="language-{label}">{highlighted}</code></pre></div>\n'
    )


def _render_code_block(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    return f"<pre><code>{html.escape(tokens[index].content)}</code></pre>\n"


def _render_inline_math(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    return latex_to_mathml(tokens[index].content, display="inline")


def _render_block_math(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    mathml = latex_to_mathml(tokens[index].content, display="block")
    return f'<div class="math-block" tabindex="0">{mathml}</div>\n'


def _render_image(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    token = tokens[index]
    src = html.escape(str(token.attrGet("src") or ""), quote=True)
    alt = html.escape(_inline_text(token), quote=True)
    caption = html.escape(str(token.attrGet("title") or ""))
    return (
        f'<figure><img src="{src}" alt="{alt}" loading="lazy">'
        f"<figcaption>{caption}</figcaption></figure>"
    )


def _sole_image(token: Token) -> bool:
    children = token.children
    return children is not None and len(children) == 1 and children[0].type == "image"


def _render_paragraph_open(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    if (
        index + 1 < len(tokens)
        and tokens[index + 1].type == "inline"
        and _sole_image(tokens[index + 1])
    ):
        return ""
    return "<p>"


def _render_paragraph_close(_renderer: object, tokens: list[Token], index: int, *_: object) -> str:
    if index > 0 and tokens[index - 1].type == "inline" and _sole_image(tokens[index - 1]):
        return "\n"
    return "</p>\n"
