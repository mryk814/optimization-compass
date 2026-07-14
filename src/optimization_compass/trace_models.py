from __future__ import annotations

import json
import math
import re
from collections.abc import Sequence
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TRACE_CONTRACT_VERSION: Literal["1.0.0"] = "1.0.0"
MAX_TRACE_FRAMES = 1_000
MAX_TRACE_BYTES = 2 * 1024 * 1024

NonBlank = Annotated[str, Field(min_length=1, pattern=r".*\S.*")]
Slug = Annotated[str, Field(min_length=1, pattern=r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")]
SupportStatus = Literal["supported", "unsupported", "unknown", "not_applicable"]
DecisionState = Literal["accepted", "rejected", "not_applicable"]
TerminalStatus = Literal[
    "completed", "converged", "budget_exhausted", "diverged", "stopped", "failed"
]


class TraceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, strict=True)


class TracePoint(TraceModel):
    point_id: NonBlank
    role: Slug
    coordinates: list[float] = Field(min_length=1)
    value: float | None
    label_ja: NonBlank
    label_en: NonBlank


class TraceVector(TraceModel):
    vector_id: NonBlank
    role: Slug
    origin: list[float] = Field(min_length=1)
    components: list[float] = Field(min_length=1)
    label_ja: NonBlank
    label_en: NonBlank

    @model_validator(mode="after")
    def validate_dimension(self) -> Self:
        if len(self.origin) != len(self.components):
            raise ValueError("vector origin and components must have the same dimension")
        return self


class TraceMetric(TraceModel):
    metric_id: NonBlank
    label_ja: NonBlank
    label_en: NonBlank
    value: float
    unit: NonBlank | None


class TraceFrame(TraceModel):
    frame_index: int = Field(ge=0)
    iteration: int = Field(ge=0)
    oracle_evaluations: int = Field(ge=0)
    elapsed_steps: int = Field(ge=0)
    elapsed_time_ms: float = Field(ge=0)
    event_type: Slug
    decision: DecisionState
    explanation_key: Slug
    event_label_ja: NonBlank | None
    event_label_en: NonBlank | None
    keyframe: bool
    points: list[TracePoint]
    vectors: list[TraceVector]
    metrics: list[TraceMetric]
    payload: object

    @field_validator("payload", mode="before")
    @classmethod
    def validate_payload_json(cls, value: object) -> object:
        _require_finite_json(value, "payload")
        return value

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if (self.event_label_ja is None) != (self.event_label_en is None):
            raise ValueError("event labels must provide both Japanese and English or neither")
        _require_unique([point.point_id for point in self.points], "point")
        _require_unique([vector.vector_id for vector in self.vectors], "vector")
        _require_unique([metric.metric_id for metric in self.metrics], "metric")
        return self


class AlgorithmTrace(TraceModel):
    contract_version: Literal["1.0.0"]
    dataset_version: NonBlank
    data_version: NonBlank
    trace_id: NonBlank
    method_id: NonBlank
    profile_id: NonBlank
    objective_id: NonBlank
    scenario_id: NonBlank
    generator_id: NonBlank
    generator_version: NonBlank
    implementation_mapping_status: SupportStatus
    implementation_id: NonBlank | None
    objective: dict[str, object]
    preset: dict[str, object]
    parameters: dict[str, object]
    initial_state: dict[str, object]
    seed: dict[str, object]
    evaluation_budget: int = Field(gt=0)
    stopping: dict[str, object]
    environment: dict[str, object]
    fairness_statement: NonBlank
    frames: list[TraceFrame] = Field(min_length=1)
    terminal_status: TerminalStatus
    terminal_summary_ja: NonBlank
    terminal_summary_en: NonBlank
    source_ids: list[NonBlank] = Field(min_length=1)

    @field_validator(
        "objective",
        "preset",
        "parameters",
        "initial_state",
        "seed",
        "stopping",
        "environment",
        mode="before",
    )
    @classmethod
    def validate_json_record(cls, value: object, info: object) -> object:
        field_name = getattr(info, "field_name", "record")
        _require_finite_json(value, str(field_name))
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return value

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        if self.implementation_mapping_status == "supported":
            if self.implementation_id is None:
                raise ValueError("supported implementation mapping requires implementation_id")
        elif self.implementation_id is not None:
            raise ValueError(
                f"{self.implementation_mapping_status} implementation mapping forbids "
                "implementation_id"
            )
        if len(self.frames) > MAX_TRACE_FRAMES:
            raise ValueError("trace exceeds maximum 1,000 frames")
        _validate_frame_progress(self.frames)
        _require_unique(self.source_ids, "source")
        raw_size = len(_canonical_model_bytes(self))
        if raw_size > MAX_TRACE_BYTES:
            raise ValueError(
                f"trace raw canonical JSON exceeds 2 MiB ({raw_size} bytes > {MAX_TRACE_BYTES})"
            )
        return self


class TraceIndexEntry(TraceModel):
    trace_id: NonBlank
    path: NonBlank
    method_id: NonBlank
    profile_id: NonBlank
    objective_id: NonBlank
    scenario_id: NonBlank
    title_ja: NonBlank
    title_en: NonBlank

    @field_validator("path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        if (
            re.fullmatch(r"[a-z0-9][a-z0-9._/-]*\.json", value) is None
            or "//" in value
            or ".." in value.split("/")
        ):
            raise ValueError("trace index path must be a safe relative URL path")
        return value


class TraceIndex(TraceModel):
    contract_version: Literal["1.0.0"]
    dataset_version: NonBlank
    data_version: NonBlank
    traces: list[TraceIndexEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_trace_ids(self) -> Self:
        _require_unique([trace.trace_id for trace in self.traces], "trace")
        return self


class TraceBundle(TraceModel):
    contract_version: Literal["1.0.0"]
    bundle_id: NonBlank
    comparison_id: NonBlank
    dataset_version: NonBlank
    data_version: NonBlank
    objective_id: NonBlank
    objective: dict[str, object]
    initial_state: dict[str, object]
    seed: dict[str, object]
    evaluation_budget: int = Field(gt=0)
    stopping: dict[str, object]
    environment: dict[str, object]
    fairness_statement: NonBlank
    member_traces: list[AlgorithmTrace] = Field(min_length=1)
    synchronization: Literal["oracle_evaluations"]

    @field_validator("objective", "initial_state", "seed", "stopping", "environment", mode="before")
    @classmethod
    def validate_json_record(cls, value: object, info: object) -> object:
        field_name = getattr(info, "field_name", "record")
        _require_finite_json(value, str(field_name))
        if not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a JSON object")
        return value

    @model_validator(mode="after")
    def validate_fairness(self) -> Self:
        _require_unique([trace.trace_id for trace in self.member_traces], "member trace")
        expected = {
            "dataset_version": self.dataset_version,
            "data_version": self.data_version,
            "objective_id": self.objective_id,
            "objective": self.objective,
            "initial_state": self.initial_state,
            "seed": self.seed,
            "evaluation_budget": self.evaluation_budget,
            "stopping": self.stopping,
            "environment": self.environment,
            "fairness_statement": self.fairness_statement,
        }
        for member in self.member_traces:
            for field_name, expected_value in expected.items():
                if getattr(member, field_name) != expected_value:
                    raise ValueError(
                        f"member trace {member.trace_id} {field_name} does not match bundle"
                    )
            if member.frames[-1].oracle_evaluations > self.evaluation_budget:
                raise ValueError(f"member trace {member.trace_id} exceeds bundle evaluation_budget")
        return self


def canonical_trace_bytes(trace: AlgorithmTrace | TraceBundle) -> bytes:
    """Serialize a validated trace contract to stable raw UTF-8 JSON bytes."""
    return _canonical_model_bytes(trace)


def _canonical_model_bytes(model: BaseModel) -> bytes:
    return json.dumps(
        model.model_dump(mode="json"),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_frame_progress(frames: Sequence[TraceFrame]) -> None:
    expected_indices = list(range(len(frames)))
    actual_indices = [frame.frame_index for frame in frames]
    if actual_indices != expected_indices:
        raise ValueError("frame_index values must be contiguous from zero")
    progress_fields = ("iteration", "oracle_evaluations", "elapsed_steps", "elapsed_time_ms")
    for field_name in progress_fields:
        values = [getattr(frame, field_name) for frame in frames]
        if any(value < 0 for value in values):
            raise ValueError(f"{field_name} must be non-negative")
        if any(current < previous for previous, current in zip(values, values[1:], strict=False)):
            raise ValueError(f"{field_name} must be monotonic")


def _require_unique(values: Sequence[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {label} IDs are not allowed")


def _require_finite_json(value: object, path: str) -> None:
    if value is None or isinstance(value, (str, bool)):
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{path} contains a non-finite number")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _require_finite_json(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{path} contains a non-string object key")
            _require_finite_json(item, f"{path}.{key}")
        return
    raise ValueError(f"{path} contains a non-JSON value of type {type(value).__name__}")


assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", TRACE_CONTRACT_VERSION)
