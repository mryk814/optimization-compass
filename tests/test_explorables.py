import json
from pathlib import Path

import pytest

from optimization_compass.content_models import load_content, parse_content
from optimization_compass.explorables import (
    Beat,
    Explorable,
    embedded_figure_ids,
    load_explorables,
    read_explorables,
)

_HEADER = """---
content_id: concept.example
kind: concept
canonical_entity_type: feature
canonical_entity_id: F_CONVEXITY
title_ja: Example
title_en: Example
summary: Summary.
source_ids: [S001]
status: draft
last_reviewed: 2026-07-15
---

"""


def _page(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "content/concepts/example.md"
    path.parent.mkdir(parents=True)
    path.write_text(_HEADER + body, encoding="utf-8")
    return path


def _figure(figures: Path, folder: str, **fields: object) -> None:
    meta = {
        "id": folder,
        "title_ja": "t",
        "question": "q。",
        "fixed_conditions": "f",
        "not_implied": "n。",
    } | fields
    (figures / folder).mkdir(parents=True)
    (figures / folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")


def test_each_figure_folder_is_read_under_its_name(tmp_path: Path) -> None:
    _figure(tmp_path, "b-figure")
    _figure(tmp_path, "a-figure")

    assert list(read_explorables(tmp_path)) == ["a-figure", "b-figure"]


def test_a_copied_figure_folder_must_rename_its_id(tmp_path: Path) -> None:
    _figure(tmp_path, "new-figure", id="old-figure")

    with pytest.raises(ValueError, match="must match its folder name 'new-figure'"):
        read_explorables(tmp_path)


def test_a_figure_folder_without_meta_json_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "half-added").mkdir()

    with pytest.raises(ValueError, match="needs a meta.json"):
        read_explorables(tmp_path)


def test_invalid_meta_json_names_its_file(tmp_path: Path) -> None:
    _figure(tmp_path, "bad-beats", beats=[{"settings": {}, "duration_s": 1}])

    with pytest.raises(ValueError, match=r"bad-beats[\\/]meta\.json"):
        read_explorables(tmp_path)


def test_registry_entries_state_question_and_limits() -> None:
    registry = load_explorables()

    assert {"gradient-descent-valley", "lp-vertex-walk", "convexity-chord"} <= set(registry)
    for entry in registry.values():
        assert entry.question.endswith("。")
        assert entry.not_implied.endswith("。")


def test_explorable_block_compiles_to_mount_point_with_visible_caption(tmp_path: Path) -> None:
    path = _page(
        tmp_path,
        "## Overview\n\nSummary.\n\n"
        "::: explorable convexity-chord\n"
        "点を動かして、線分とグラフの上下を確かめます。\n"
        ":::\n\n"
        "## After\n\nText.\n",
    )

    page = parse_content(path)

    assert 'data-explorable-id="convexity-chord"' in page.html
    assert "data-explorable-mount" in page.html
    assert '<figcaption class="explorable-caption"><p>点を動かして' in page.html
    assert "</p>\n</figcaption></figure>" in page.html
    assert [heading.label for heading in page.toc] == ["Overview", "After"]


@pytest.mark.parametrize(
    ("block", "message"),
    [
        ("::: explorable no-such-figure\nCaption.\n:::", "unknown explorable id"),
        ("::: explorable\nCaption.\n:::", "exactly one kebab-case id"),
        ("::: explorable Bad_Id\nCaption.\n:::", "exactly one kebab-case id"),
        ("::: explorable convexity-chord\n:::", "exactly one caption paragraph"),
        (
            "::: explorable convexity-chord\nOne.\n\nTwo.\n:::",
            "exactly one caption paragraph",
        ),
        (
            "::: explorable convexity-chord\n- item\n:::",
            "exactly one caption paragraph",
        ),
        (
            '::: explorable convexity-chord\n![a](https://example.com/a.png "c")\n:::',
            "caption must be text",
        ),
        (
            "::: explorable convexity-chord\nA.\n:::\n\n::: explorable convexity-chord\nB.\n:::",
            "used more than once",
        ),
        (
            "- item\n\n  ::: explorable convexity-chord\n  Caption.\n  :::",
            "top-level block",
        ),
    ],
)
def test_explorable_block_rejects_invalid_authoring(
    tmp_path: Path, block: str, message: str
) -> None:
    path = _page(tmp_path, f"## Overview\n\nSummary.\n\n{block}\n")

    with pytest.raises(ValueError, match=message):
        parse_content(path)


def test_published_articles_only_use_registered_explorables() -> None:
    root = Path(__file__).resolve().parents[1]
    registry = set(load_explorables())
    used: set[str] = set()

    for page in load_content(root / "content"):
        used.update(embedded_figure_ids(page.body))

    assert used <= registry
    assert used, "at least one article should embed an explorable"


def test_guided_scene_beats_are_sentences_within_the_length_budget() -> None:
    beats = load_explorables()["gradient-descent-valley"].beats

    assert beats
    assert sum(beat.duration_s for beat in beats) <= 60
    for beat in beats:
        assert beat.caption_ja.endswith("。")
        assert beat.narration_ja.endswith("。")


@pytest.mark.parametrize(
    ("beat", "message"),
    [
        ({"duration_s": 1}, "between 2 and 15 seconds"),
        ({"caption_ja": "句点がない"}, "ending with 。"),
        ({"narration_ja": " "}, "ending with 。"),
        ({"extra": 1}, "Extra inputs"),
    ],
)
def test_beats_reject_invalid_authoring(beat: dict[str, object], message: str) -> None:
    valid = {
        "settings": {"eta": 0.1},
        "duration_s": 5,
        "caption_ja": "見る。",
        "narration_ja": "話す。",
    }
    with pytest.raises(ValueError, match=message):
        Beat.model_validate(valid | beat)


def test_guided_scene_must_fit_in_a_minute() -> None:
    beat = {"settings": {}, "duration_s": 15, "caption_ja": "見る。", "narration_ja": "話す。"}
    entry = {
        "id": "x",
        "title_ja": "t",
        "question": "q。",
        "fixed_conditions": "f",
        "not_implied": "n。",
        "beats": [beat] * 5,
    }
    with pytest.raises(ValueError, match="must not exceed 60 seconds"):
        Explorable.model_validate(entry)


_PARAMS = {
    "eta": {"type": "number", "min": 0.0, "max": 1.0},
    "kappa": {"type": "integer", "min": 1, "max": 40},
    "mode": {"type": "choice", "choices": ["grid", "random"]},
}


def _entry(**fields: object) -> dict[str, object]:
    return {
        "id": "x",
        "title_ja": "t",
        "question": "q。",
        "fixed_conditions": "f",
        "not_implied": "n。",
    } | fields


def _beat(**settings: object) -> dict[str, object]:
    return {"settings": settings, "duration_s": 5, "caption_ja": "見る。", "narration_ja": "話す。"}


def test_params_declare_what_beats_may_set() -> None:
    entry = Explorable.model_validate(
        _entry(params=_PARAMS, beats=[_beat(eta=0.5, kappa=20, mode="random")])
    )

    assert entry.params is not None
    assert set(entry.params) == {"eta", "kappa", "mode"}


@pytest.mark.parametrize(
    ("param", "message"),
    [
        ({"type": "number", "min": 1, "max": 1}, "needs min < max"),
        ({"type": "number", "min": 0}, "needs min < max"),
        ({"type": "integer", "min": 0.5, "max": 3}, "whole-number min and max"),
        ({"type": "number", "min": 0, "max": 1, "choices": ["a", "b"]}, "not choices"),
        ({"type": "choice", "choices": ["only"]}, "at least two distinct choices"),
        ({"type": "choice", "choices": ["a", "a"]}, "at least two distinct choices"),
        ({"type": "choice", "choices": ["a", "b c"]}, "words of letters"),
        ({"type": "choice", "choices": ["a", "b"], "min": 0}, "not min / max"),
        ({"type": "text"}, "Input should be"),
        ({"type": "number", "min": 0, "max": 1, "default": 2}, "default 2.0 must be within 0..1"),
        ({"type": "integer", "min": 0, "max": 9, "default": 1.5}, "must be a whole number"),
        ({"type": "choice", "choices": ["a", "b"], "default": "c"}, "must be one of a, b"),
    ],
)
def test_params_reject_invalid_declarations(param: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        Explorable.model_validate(_entry(params={"p": param}))


@pytest.mark.parametrize("name", ["seconds", "predict", "answer", "Eta", "my-param"])
def test_param_names_stay_clear_of_step_keys(name: str) -> None:
    with pytest.raises(ValueError, match="param name"):
        Explorable.model_validate(_entry(params={name: _PARAMS["eta"]}))


@pytest.mark.parametrize(
    ("settings", "message"),
    [
        ({"speed": 1}, "'speed', which params does not declare"),
        ({"eta": 1.5}, "must be within 0..1"),
        ({"eta": "fast"}, "must be a number"),
        ({"kappa": 2.5}, "must be a whole number"),
        ({"mode": "sobol"}, "must be one of grid, random"),
    ],
)
def test_beats_are_checked_against_declared_params(
    settings: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        Explorable.model_validate(_entry(params=_PARAMS, beats=[_beat(**settings)]))


def test_beats_of_a_figure_without_params_stay_unchecked() -> None:
    entry = Explorable.model_validate(_entry(beats=[_beat(anything=1)]))

    assert entry.params is None


def test_embedded_figures_are_found_in_explorable_and_lesson_blocks() -> None:
    body = "::: explorable a-figure\nC.\n:::\n\n:::: lesson b-figure\n::: step\nS。\n:::\n::::\n"

    assert embedded_figure_ids(body) == ("a-figure", "b-figure")
