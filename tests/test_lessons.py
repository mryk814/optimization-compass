"""`:::: lesson <figure-id>` blocks: one step of prose drives one beat of the figure."""

import json
import re
from html import unescape
from pathlib import Path

import pytest

from optimization_compass import content_markdown
from optimization_compass.content_markdown import render_markdown
from optimization_compass.explorables import Explorable

_PATH = Path("content/concepts/example.md")
_FIGURE = "gradient-descent-valley"  # declares method, eta, kappa (integer), beta, x0, y0, iter


def _lesson(*steps: str, figure: str = _FIGURE) -> str:
    return f":::: lesson {figure}\n" + "\n".join(steps) + "\n::::"


def _step(info: str = "", body: str = "ここを見ます。続きの説明です。") -> str:
    return f"::: step {info}\n{body}\n:::"


def _render(block: str) -> str:
    return render_markdown(f"## 見出し\n\n要約です。\n\n{block}\n", path=_PATH).html


def _steps(html: str) -> list[dict[str, str]]:
    return [
        {name: unescape(value) for name, value in re.findall(r'(data-[a-z-]+)="([^"]*)"', tag)}
        for tag in re.findall(r"<li class=\"lesson-step\"[^>]*>", html)
    ]


def test_lesson_compiles_to_a_figure_mount_and_an_ordered_list_of_steps() -> None:
    html = _render(
        _lesson(
            _step(
                "seconds=8 eta=0.02 iter=0..100", "**小さい学習率では遅い。** $\\eta$ が小さい。"
            ),
            _step("kappa=1..20@4 method=momentum"),
        )
    )

    assert f'<section class="lesson" data-lesson-figure="{_FIGURE}">' in html
    assert f'data-explorable-id="{_FIGURE}"' in html
    assert "data-explorable-mount" in html and "explorable-fallback" in html
    assert "data-lesson-nav" in html
    assert html.count('<ol class="lesson-steps">') == 1 and "</ol></section>" in html
    first, second = _steps(html)
    defaults = {"method": "gd", "kappa": 20, "beta": 0.5, "x0": 4, "y0": 3}
    assert first["data-seconds"] == "8"
    # Every step carries the figure's whole state: what it sets, and defaults for the rest.
    assert json.loads(first["data-settings"]) == defaults | {
        "eta": 0.02,
        "iter": {"from": 0, "to": 100},
    }
    assert first["data-caption"] == "小さい学習率では遅い。"
    assert second["data-seconds"] == "6"
    # kappa is an integer param, so its moving value advances in whole steps.
    assert json.loads(second["data-settings"]) == defaults | {
        "eta": 0.02,
        "iter": 100,
        "kappa": {"from": 1, "to": 20, "rate": 4, "step": 1},
        "method": "momentum",
    }
    # Step bodies are ordinary article prose: emphasis and math render as everywhere else.
    assert "<strong>小さい学習率では遅い。</strong>" in html
    assert "<math" in html


def test_predict_step_marks_its_choices_and_answer() -> None:
    html = _render(
        _lesson(
            _step(
                "predict answer=2",
                "どれが残るか、先に選んでください。\n\n- 収束する\n- 発散する\n- 止まる",
            ),
            _step(),
        )
    )

    predict, plain = _steps(html)
    assert predict["data-predict"] == "" and predict["data-answer"] == "2"
    assert predict["data-caption"] == "どれが残るか、先に選んでください。"
    assert '<ul class="lesson-choices" data-lesson-choices="">' in html
    assert "data-predict" not in plain and "data-answer" not in plain


def test_a_step_keeps_what_the_previous_step_ended_on() -> None:
    html = _render(
        _lesson(
            _step("seconds=6 eta=0.1 iter=0..30 kappa=1..40@2.5"),
            _step("eta=0.2"),
            _step("seconds=4 iter=30..0@5"),
            _step(),
        )
    )

    settings = [json.loads(step["data-settings"]) for step in _steps(html)]
    # A sweep ends on its far end; a rate ends where its seconds take it (2.5/s for 6 s from 1,
    # in whole steps for an integer param).
    assert (settings[1]["eta"], settings[1]["iter"], settings[1]["kappa"]) == (0.2, 30, 16)
    assert settings[2]["iter"] == {"from": 30, "to": 0, "rate": 5}
    assert (settings[3]["eta"], settings[3]["iter"], settings[3]["kappa"]) == (0.2, 10, 16)


def test_the_first_step_must_set_every_param_without_a_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    figure = Explorable.model_validate(
        {
            "id": "two-knobs",
            "title_ja": "t",
            "question": "q。",
            "fixed_conditions": "f",
            "not_implied": "n。",
            "params": {
                "a": {"type": "number", "min": 0, "max": 1},
                "b": {"type": "number", "min": 0, "max": 1, "default": 0.5},
                "layer": {"type": "choice", "choices": ["plan", "answer"]},
            },
        }
    )
    monkeypatch.setattr(content_markdown, "load_explorables", lambda: {figure.id: figure})

    html = _render(_lesson(_step("a=0.2 layer=plan"), _step("layer=answer"), figure="two-knobs"))
    assert [json.loads(step["data-settings"]) for step in _steps(html)] == [
        {"a": 0.2, "b": 0.5, "layer": "plan"},
        {"a": 0.2, "b": 0.5, "layer": "answer"},
    ]
    with pytest.raises(ValueError, match="step 1: a, layer is not set and has no default"):
        _render(_lesson(_step("b=0.1"), _step("a=0.2 layer=plan"), figure="two-knobs"))


def test_a_step_caption_without_a_full_stop_is_the_whole_first_paragraph() -> None:
    html = _render(_lesson(_step(body="句点のない一文"), _step()))

    assert _steps(html)[0]["data-caption"] == "句点のない一文"


def test_step_bodies_keep_the_article_rules() -> None:
    with pytest.raises(ValueError, match="raw HTML is forbidden"):
        _render(_lesson(_step(body="本文。\n\n<b>強調</b>"), _step()))
    with pytest.raises(ValueError, match="unsupported fenced code language"):
        _render(_lesson(_step(body="本文。\n\n```ruby\nputs 1\n```"), _step()))


_TWO = _step() + "\n" + _step()


@pytest.mark.parametrize(
    ("block", "message"),
    [
        (":::: lesson\n" + _TWO + "\n::::", "exactly one kebab-case figure id"),
        (_lesson(_TWO, figure="Bad_Id"), "exactly one kebab-case figure id"),
        (_lesson(_TWO, figure="no-such-figure"), "unknown explorable id"),
        (_lesson(_TWO, figure="convexity-chord"), "must declare params"),
        (_lesson(_TWO) + "\n\n" + _lesson(_TWO), "used more than once"),
        (_lesson(_TWO) + f"\n\n::: explorable {_FIGURE}\n説明。\n:::", "used more than once"),
        (f"::: explorable {_FIGURE}\n説明。\n:::\n\n" + _lesson(_TWO), "used more than once"),
        ("::: note\n" + _lesson(_TWO) + "\n:::", "must be a top-level block"),
        (_step(), "must be directly inside a lesson"),
        (_lesson(_step(), "段の外の文。", _step()), "only `::: step` blocks"),
        (_lesson(_step()), "2 to 12 steps, found 1"),
        (_lesson(*[_step("seconds=2")] * 13), "2 to 12 steps, found 13"),
        (_lesson(*[_step("seconds=15")] * 9), "must not exceed 120 seconds"),
        (_lesson(_step("seconds=1"), _step()), "seconds must be a number from 2 to 15"),
        (_lesson(_step("seconds=16"), _step()), "seconds must be a number from 2 to 15"),
        (_lesson(_step("seconds=2..5"), _step()), "seconds must be a number from 2 to 15"),
        (_lesson(_step("eta=0.1 eta=0.2"), _step()), "key is given twice: eta"),
        (_lesson(_step("eta"), _step()), "write keys as key=value"),
        (_lesson(_step("eta="), _step()), "write keys as key=value"),
        (_lesson(_step("speed=3"), _step()), "'speed' is not a param of gradient-descent-valley"),
        (_lesson(_step("eta=fast"), _step()), "must be a number, a..b or a..b@rate"),
        (_lesson(_step("eta=0.9"), _step()), "must be within 0.005..0.3"),
        (_lesson(_step("kappa=2.5"), _step()), "must be a whole number"),
        (_lesson(_step("kappa=1..2.5"), _step()), "2.5 must be a whole number"),
        (_lesson(_step("iter=0..120"), _step()), "120 must be within 0..100"),
        (_lesson(_step("iter=5..5"), _step()), "two different ends"),
        (_lesson(_step("iter=0..30@0"), _step()), "rate after @ must be positive"),
        (_lesson(_step("method=newton"), _step()), "must be one of gd, momentum"),
        (_lesson(_step("method=1..2"), _step()), "only a number param can sweep"),
        (_lesson(_step(body="- 文のない段"), _step()), "needs a paragraph of text"),
        (_lesson(_step(body="本文。\n\n### 見出し"), _step()), "must not contain a heading"),
        (
            _lesson(_step(body="本文。\n\n::: step\n入れ子。\n:::"), _step()),
            "must not contain another lesson or step",
        ),
        # The figure block's closing `:::` ends the step early, so the lesson no longer parses.
        (
            _lesson(_step(body="本文。\n\n::: explorable convexity-chord\n説明。\n:::"), _step()),
            "only `::: step` blocks",
        ),
        (
            _lesson(_step("predict=yes answer=1", "問い。\n\n- A\n- B"), _step()),
            "predict is a flag",
        ),
        (_lesson(_step("predict", "問い。\n\n- A\n- B"), _step()), "needs answer=1..2"),
        (_lesson(_step("predict answer=3", "問い。\n\n- A\n- B"), _step()), "needs answer=1..2"),
        (_lesson(_step("predict answer=0", "問い。\n\n- A\n- B"), _step()), "needs answer=1..2"),
        (
            _lesson(_step("predict answer=x", "問い。\n\n- A\n- B"), _step()),
            "answer must be the number",
        ),
        (_lesson(_step("predict answer=1", "問い。"), _step()), "exactly one list"),
        (
            _lesson(_step("predict answer=1", "問い。\n\n- A\n- B\n\n文。\n\n1. C\n2. D"), _step()),
            "exactly one list",
        ),
        (_lesson(_step("predict answer=1", "問い。\n\n- A"), _step()), "2 to 4 choices, found 1"),
        (
            _lesson(_step("predict answer=1", "問い。\n\n- A\n- B\n- C\n- D\n- E"), _step()),
            "2 to 4 choices, found 5",
        ),
        (_lesson(_step("answer=1"), _step()), "answer is only for a predict step"),
    ],
)
def test_lesson_rejects_invalid_authoring(block: str, message: str) -> None:
    with pytest.raises(ValueError, match=re.escape(message)):
        _render(block)
