from __future__ import annotations

import json
from pathlib import Path

import pytest

from optimization_compass.language_mixing import (
    PENDING_PATH,
    SURFACES,
    mixed_words,
    pending_document,
    require_language_contract,
    surface_hits,
)

ROOT = Path(__file__).parents[1]


def test_mixed_words_flags_ordinary_english_inside_japanese() -> None:
    assert mixed_words("SO(3)上でnear-piのattitudeを合わせる") == ["near-pi", "attitude"]
    assert mixed_words("feasible iterateと収束claimを分離") == ["feasible", "iterate", "claim"]


def test_mixed_words_keeps_names_code_formulas_and_glosses() -> None:
    text = (
        "Newton法とBFGSをQR分解で比べ、$\\exp(\\hat\\delta)$ と `np.linalg.svd` を使う。"
        "目的関数（objective function）は[記事](#/learn/concept.manifold)と"
        "https://example.org/some-page にある。一歩は0.5 radで、log の底はe。"
    )
    assert mixed_words(text) == []


def test_mixed_words_ignores_strings_without_japanese() -> None:
    assert mixed_words("deterministic / not applicable") == []


def _write_surfaces(root: Path, gallery_text: str, pending: dict[str, list[str]]) -> None:
    payloads = {
        "gallery": {
            "cases": [
                {
                    "case_id": "case-a",
                    "title_ja": gallery_text,
                    "title_en": "an English title",
                    "python_example": "# コメント with words",
                }
            ]
        },
        "comparison": {"comparisons": [{"comparison_id": "COMPARE_A", "title_ja": "比べる"}]},
        "scenario": {"scenarios": [{"scenario_id": "SCENARIO_A", "title_ja": "見る"}]},
    }
    for surface, (path, _, _) in SURFACES.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(json.dumps(payloads[surface], ensure_ascii=False), "utf-8")
    (root / PENDING_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / PENDING_PATH).write_text(
        json.dumps({"contract_version": "1.0.0", "pending": pending}), "utf-8"
    )


def test_english_fields_and_code_examples_are_not_checked(tmp_path: Path) -> None:
    _write_surfaces(tmp_path, "回転を合わせる", {})
    assert surface_hits(tmp_path, "gallery") == {"case-a": []}


def test_new_mixed_item_outside_the_pending_list_fails(tmp_path: Path) -> None:
    _write_surfaces(tmp_path, "attitudeを合わせる", {})
    with pytest.raises(ValueError, match="gallery:case-a \\(attitude\\)"):
        require_language_contract(tmp_path)


def test_pending_item_is_allowed_and_reported_once_clean(tmp_path: Path) -> None:
    _write_surfaces(tmp_path, "attitudeを合わせる", {"gallery": ["case-a"]})
    assert require_language_contract(tmp_path) == ()
    _write_surfaces(tmp_path, "向きを合わせる", {"gallery": ["case-a"]})
    assert require_language_contract(tmp_path) == (("gallery", "case-a"),)


def test_pending_list_rejects_unknown_items(tmp_path: Path) -> None:
    _write_surfaces(tmp_path, "向きを合わせる", {"gallery": ["case-b"]})
    with pytest.raises(ValueError, match="unknown items: gallery:case-b"):
        require_language_contract(tmp_path)


def test_repository_items_are_clean_or_pending() -> None:
    require_language_contract(ROOT)


def test_pending_list_is_sorted_and_canonical() -> None:
    raw = json.loads((ROOT / PENDING_PATH).read_text(encoding="utf-8"))
    keys = {
        (surface, item_id)  # type: ignore[misc]
        for surface, ids in raw["pending"].items()
        for item_id in ids
    }
    assert raw == pending_document(keys)  # type: ignore[arg-type]
