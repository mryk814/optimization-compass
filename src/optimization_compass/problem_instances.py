from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NonBlank = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
ObjectiveDirection = Literal["minimize", "maximize", "multiobjective"]
KnownReferenceStatus = Literal[
    "known_exact",
    "known_reference",
    "best_known",
    "unknown",
    "not_meaningful",
]
SeedStatus = Literal["fixed", "not_applicable", "unknown"]


class ProblemModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProblemDefinition(ProblemModel):
    problem_definition_id: NonBlank
    name_ja: NonBlank
    name_en: NonBlank
    mathematical_family: NonBlank
    variable_domain: NonBlank
    objective_form: NonBlank
    objective_direction: ObjectiveDirection
    available_oracles: list[NonBlank] = Field(min_length=1)
    constraint_class: NonBlank
    dimensionality_policy: dict[str, object]
    known_reference_semantics: NonBlank
    related_problem_ids: list[NonBlank] = Field(min_length=1)
    feature_ids: list[NonBlank] = Field(min_length=1)
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_collections(self) -> ProblemDefinition:
        for label, values in (
            ("available_oracles", self.available_oracles),
            ("related_problem_ids", self.related_problem_ids),
            ("feature_ids", self.feature_ids),
            ("source_ids", self.source_ids),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {label} values are not allowed")
        if not self.dimensionality_policy:
            raise ValueError("dimensionality_policy must not be empty")
        return self


class ProblemInstance(ProblemModel):
    problem_instance_id: NonBlank
    problem_definition_id: NonBlank
    name_ja: NonBlank
    name_en: NonBlank
    registry_key: NonBlank
    dimension: int = Field(ge=1)
    parameters: dict[str, object]
    bounds: dict[str, object]
    constraints: list[dict[str, object]]
    initialization_candidates: list[dict[str, object]] = Field(min_length=1)
    seed_status: SeedStatus
    seed_value: int | None
    known_reference_status: KnownReferenceStatus
    known_reference: dict[str, object] | None
    display: dict[str, object]
    intended_phenomena: list[NonBlank] = Field(min_length=1)
    limitations_ja: NonBlank
    limitations_en: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)
    last_verified: NonBlank

    @model_validator(mode="after")
    def validate_conditionals(self) -> ProblemInstance:
        if (self.seed_status == "fixed") != (self.seed_value is not None):
            raise ValueError("fixed seed requires a value; other states forbid one")
        reference_required = self.known_reference_status in {
            "known_exact",
            "known_reference",
            "best_known",
        }
        if reference_required != (self.known_reference is not None):
            raise ValueError("known reference status and payload must agree")
        if not self.parameters or not self.bounds or not self.display:
            raise ValueError("parameters, bounds, and display metadata must not be empty")
        if len(self.intended_phenomena) != len(set(self.intended_phenomena)):
            raise ValueError("duplicate intended phenomena are not allowed")
        if len(self.source_ids) != len(set(self.source_ids)):
            raise ValueError("duplicate source IDs are not allowed")
        if self.known_reference is not None:
            reference_sources = self.known_reference.get("source_ids")
            if not isinstance(reference_sources, list) or not reference_sources:
                raise ValueError("known_reference must include source_ids")
            if not set(reference_sources) <= set(self.source_ids):
                raise ValueError("known_reference sources must be instance sources")
        return self


class ProblemSuiteSeed(ProblemModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    definitions: list[ProblemDefinition] = Field(min_length=1)
    instances: list[ProblemInstance] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_closure(self) -> ProblemSuiteSeed:
        definition_ids = [item.problem_definition_id for item in self.definitions]
        instance_ids = [item.problem_instance_id for item in self.instances]
        registry_keys = [item.registry_key for item in self.instances]
        for label, values in (
            ("problem definition", definition_ids),
            ("problem instance", instance_ids),
            ("registry key", registry_keys),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {label} values are not allowed")
        known_definitions = set(definition_ids)
        for instance in self.instances:
            if instance.problem_definition_id not in known_definitions:
                raise ValueError(
                    f"instance definition does not resolve: {instance.problem_instance_id}"
                )
        return self


class ProblemCatalog(ProblemModel):
    contract_version: Literal["1.0.0"] = "1.0.0"
    dataset_version: NonBlank
    definitions: list[ProblemDefinition] = Field(min_length=1)
    instances: list[ProblemInstance] = Field(min_length=1)
