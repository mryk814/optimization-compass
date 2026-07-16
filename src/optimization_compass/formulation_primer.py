from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PrimerModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PrimerTerm(PrimerModel):
    term_id: str = Field(min_length=1)
    term_ja: str = Field(min_length=1)
    term_en: str = Field(min_length=1)
    definition: str = Field(min_length=1)
    common_confusion: str = Field(min_length=1)


class FormulationField(PrimerModel):
    field_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    label_ja: str = Field(min_length=1)
    label_en: str = Field(min_length=1)
    beginner_description: str = Field(min_length=1)
    term_ids: list[str] = Field(min_length=1)


class TerminologyGroup(PrimerModel):
    group_id: str = Field(min_length=1)
    title_ja: str = Field(min_length=1)
    term_ids: list[str] = Field(min_length=1)


class DiagnosisFieldMapping(PrimerModel):
    question_id: str = Field(pattern=r"^Q\d{2}$")
    field_id: str = Field(min_length=1)
    cue_ja: str = Field(min_length=1)
    term_ids: list[str] = Field(min_length=1)


class FormulationPrimerIndex(PrimerModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: str = Field(min_length=1)
    generated_at: datetime
    formula_aria_label_ja: str = Field(min_length=1)
    fields: list[FormulationField] = Field(min_length=4)
    terminology_groups: list[TerminologyGroup] = Field(min_length=1)
    diagnosis_mappings: list[DiagnosisFieldMapping] = Field(min_length=1)
    terms: list[PrimerTerm] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        _require_unique([term.term_id for term in self.terms], "term")
        _require_unique([field.field_id for field in self.fields], "field")
        _require_unique(
            [mapping.question_id for mapping in self.diagnosis_mappings],
            "diagnosis question",
        )
        field_ids = {field.field_id for field in self.fields}
        term_ids = {term.term_id for term in self.terms}
        for owner, references in [
            *((f"field {field.field_id}", field.term_ids) for field in self.fields),
            *((f"group {group.group_id}", group.term_ids) for group in self.terminology_groups),
            *(
                (f"diagnosis {mapping.question_id}", mapping.term_ids)
                for mapping in self.diagnosis_mappings
            ),
        ]:
            _require_unique(references, f"{owner} term reference")
            missing = set(references) - term_ids
            if missing:
                raise ValueError(
                    f"{owner} has missing term references: {', '.join(sorted(missing))}"
                )
        for mapping in self.diagnosis_mappings:
            if mapping.field_id not in field_ids:
                raise ValueError(
                    f"diagnosis {mapping.question_id} has missing field: {mapping.field_id}"
                )
        return self


FIELD_ROWS = [
    (
        "decision_variables",
        "x",
        "決めるもの",
        "Decision variables",
        "手法が探す答え。温度・個数・材料の並びなどです。",
        ["G085"],
    ),
    (
        "variable_domain",
        "x ∈ X",
        "選べる範囲",
        "Variable domain",
        "xが取り得る値の種類と範囲です。",
        ["G087"],
    ),
    (
        "objective",
        "f(x)",
        "良くしたいもの",
        "Objective",
        "費用・誤差・時間など、小さくまたは大きくしたい値です。",
        ["G086", "G100", "G101"],
    ),
    (
        "constraints",
        "g(x), h(x)",
        "守る条件",
        "Constraints",
        "上限・品質・収支など、答えが満たす必要のある条件です。",
        ["G088", "G016", "G089"],
    ),
    (
        "evaluation_oracle",
        "oracle(x)",
        "試した結果の得方",
        "Evaluation oracle",
        "式・simulation・実験など、xを試して目的と制約を知る方法です。",
        ["G098", "G103"],
    ),
    (
        "search_goal",
        "goal",
        "どこまで探すか",
        "Search goal",
        "局所解でよいか、大域候補や証明まで必要かを決めます。",
        ["G009", "G010", "G012"],
    ),
    (
        "use_context",
        "context",
        "解き方の条件",
        "Use context",
        "一度だけか、繰り返すか、並列計算できるかという運用条件です。",
        ["G041", "G043", "G044"],
    ),
]

GROUP_ROWS = [
    (
        "variable_domains",
        "xの種類（variable domain）",
        ["G090", "G091", "G092", "G093", "G094", "G095", "G096"],
    ),
    (
        "evaluation",
        "評価の性質（evaluation）",
        ["G097", "G034", "G033", "G098", "G103", "G039", "G041"],
    ),
    (
        "objectives_and_guarantees",
        "目的と保証（objective / guarantee）",
        ["G099", "G077", "G100", "G101", "G016", "G089", "G009", "G010", "G012", "G102"],
    ),
]

DIAGNOSIS_ROWS = [
    ("Q01", "variable_domain", "x ∈ X：決める値の種類", ["G087", "G090", "G091", "G092", "G093"]),
    ("Q02", "evaluation_oracle", "oracle(x)：結果の計算方法", ["G098", "G033"]),
    ("Q03", "objective", "f(x)：良くしたい値の形", ["G086", "G099", "G077"]),
    ("Q04", "constraints", "g(x), h(x)：守る条件", ["G088", "G016"]),
    ("Q05", "evaluation_oracle", "oracle(x)：微分できる対象と情報", ["G097", "G034"]),
    ("Q06", "evaluation_oracle", "oracle(x)：1回の評価費用", ["G103", "G041"]),
    ("Q07", "evaluation_oracle", "oracle(x)：同じxでのばらつき", ["G039", "G098"]),
    ("Q08", "decision_variables", "x：決める値の数", ["G085"]),
    ("Q09", "search_goal", "goal：局所か大域か", ["G009", "G010"]),
    ("Q10", "search_goal", "goal：必要な保証", ["G012", "G102"]),
    ("Q11", "variable_domain", "X：利用できる問題構造", ["G087"]),
    ("Q12", "use_context", "context：解く頻度と計算環境", ["G041", "G043", "G044"]),
]


def build_formulation_primer_index(
    *, dataset_version: str, generated_at: datetime, glossary_rows: list[dict[str, Any]]
) -> FormulationPrimerIndex:
    fields = [
        FormulationField(
            field_id=row[0],
            symbol=row[1],
            label_ja=row[2],
            label_en=row[3],
            beginner_description=row[4],
            term_ids=row[5],
        )
        for row in FIELD_ROWS
    ]
    groups = [
        TerminologyGroup(group_id=row[0], title_ja=row[1], term_ids=row[2]) for row in GROUP_ROWS
    ]
    mappings = [
        DiagnosisFieldMapping(question_id=row[0], field_id=row[1], cue_ja=row[2], term_ids=row[3])
        for row in DIAGNOSIS_ROWS
    ]
    required_ids = {
        term_id
        for references in [
            *(field.term_ids for field in fields),
            *(group.term_ids for group in groups),
            *(mapping.term_ids for mapping in mappings),
        ]
        for term_id in references
    }
    glossary_ids = [str(row["term_id"]) for row in glossary_rows]
    _require_unique(glossary_ids, "glossary term")
    glossary_by_id = dict(zip(glossary_ids, glossary_rows, strict=True))
    missing = required_ids - glossary_by_id.keys()
    if missing:
        raise ValueError(
            f"formulation primer glossary terms are missing: {', '.join(sorted(missing))}"
        )
    terms = [
        PrimerTerm(
            term_id=term_id,
            term_ja=str(glossary_by_id[term_id]["term_ja"]),
            term_en=str(glossary_by_id[term_id]["term_en"]),
            definition=str(glossary_by_id[term_id]["definition"]),
            common_confusion=str(glossary_by_id[term_id]["common_confusion"]),
        )
        for term_id in sorted(required_ids)
    ]
    return FormulationPrimerIndex(
        dataset_version=dataset_version,
        generated_at=generated_at,
        formula_aria_label_ja="xがXに属する範囲でf(x)を最小化し、g_i(x)が0以下、h_j(x)が0に等しい制約を守る",
        fields=fields,
        terminology_groups=groups,
        diagnosis_mappings=mappings,
        terms=terms,
    )


def _require_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} IDs must be unique")
