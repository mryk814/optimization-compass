from datetime import UTC, datetime

import pytest

from optimization_compass.formulation_primer import build_formulation_primer_index


def glossary_rows() -> list[dict[str, str]]:
    from optimization_compass.formulation_primer import DIAGNOSIS_ROWS, FIELD_ROWS, GROUP_ROWS

    ids = {
        term_id
        for references in [
            *(row[-1] for row in FIELD_ROWS),
            *(row[-1] for row in GROUP_ROWS),
            *(row[-1] for row in DIAGNOSIS_ROWS),
        ]
        for term_id in references
    }
    return [
        {
            "term_id": term_id,
            "term_ja": term_id,
            "term_en": term_id,
            "definition": "definition",
            "common_confusion": "confusion",
        }
        for term_id in sorted(ids)
    ]


def test_builds_one_reference_checked_primer_for_all_diagnosis_questions() -> None:
    primer = build_formulation_primer_index(
        dataset_version="test", generated_at=datetime.now(UTC), glossary_rows=glossary_rows()
    )
    assert [mapping.question_id for mapping in primer.diagnosis_mappings] == [
        f"Q{index:02d}" for index in range(1, 13)
    ]
    assert (
        next(field for field in primer.fields if field.field_id == "variable_domain").symbol
        == "x ∈ X"
    )


def test_rejects_missing_and_duplicate_glossary_terms() -> None:
    rows = glossary_rows()
    with pytest.raises(ValueError, match="missing"):
        build_formulation_primer_index(
            dataset_version="test", generated_at=datetime.now(UTC), glossary_rows=rows[1:]
        )
    with pytest.raises(ValueError, match="unique"):
        build_formulation_primer_index(
            dataset_version="test", generated_at=datetime.now(UTC), glossary_rows=[*rows, rows[0]]
        )
