from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
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
    _validate_figures_are_standalone(tokens, path)
    _validate_and_prepare_links(tokens, headings, path)
    _validate_code_languages(tokens, path)
    summary = _first_paragraph(tokens, path)
    return RenderedMarkdown(
        html=parser.renderer.render(tokens, parser.options, {}).strip(),
        toc=tuple(headings),
        summary=summary,
    )


def render_inline_markdown(source: str) -> str:
    """Render trusted short metadata with the same math pipeline as articles."""
    if not source.strip():
        raise ValueError("inline Markdown source must not be blank")
    return _markdown_parser().renderInline(source).strip()


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
