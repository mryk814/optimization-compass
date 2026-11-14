"""Read and run an article's Python block, for the tests that compare it with a lesson module."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]


def article_code(name: str) -> str:
    article = (ROOT / f"content/concepts/{name}.md").read_text(encoding="utf-8")
    return article.split("```python\n", 1)[1].split("```", 1)[0]


def article_setup(name: str, marker: str) -> dict[str, object]:
    """Run an article's definitions without the solver calls that follow ``marker``."""
    namespace: dict[str, object] = {}
    setup = article_code(name).split(marker, 1)[0]
    exec(compile(setup, f"{name}.md", "exec"), namespace)
    return namespace


def assert_article_prints_its_comments(name: str) -> None:
    import contextlib
    import io
    import warnings

    import pytest

    pytest.importorskip("scipy.optimize")
    code = article_code(name)
    expected = [line[len("# → ") :] for line in code.splitlines() if line.startswith("# → ")]
    output = io.StringIO()
    with warnings.catch_warnings(), contextlib.redirect_stdout(output):
        warnings.simplefilter("ignore", RuntimeWarning)
        exec(compile(code, f"{name}.md", "exec"), {})
    assert output.getvalue().splitlines() == expected
