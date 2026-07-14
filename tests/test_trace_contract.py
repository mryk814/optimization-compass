from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
from pydantic import ValidationError

from optimization_compass.trace_models import (
    AlgorithmTrace,
    TraceBundle,
    TraceFrame,
    TraceIndex,
    TraceMetric,
    TracePoint,
    TraceVector,
    canonical_trace_bytes,
)
from optimization_compass.traces.base import downsample_frames, synchronize_bundle


def frame(
    index: int,
    *,
    evaluations: int | None = None,
    event_type: str = "iterate",
    keyframe: bool = False,
    payload: object | None = None,
) -> TraceFrame:
    return TraceFrame(
        frame_index=index,
        iteration=index,
        oracle_evaluations=index if evaluations is None else evaluations,
        elapsed_steps=index,
        elapsed_time_ms=float(index * 10),
        event_type=event_type,
        decision="not_applicable",
        explanation_key=f"trace.{event_type}",
        event_label_ja=None,
        event_label_en=None,
        keyframe=keyframe,
        points=[
            TracePoint(
                point_id="candidate",
                role="candidate",
                coordinates=[float(index), float(index + 1)],
                value=float(index),
                label_ja="候補点",
                label_en="Candidate",
            )
        ],
        vectors=[
            TraceVector(
                vector_id="direction",
                role="direction",
                origin=[float(index), float(index + 1)],
                components=[1.0, -1.0],
                label_ja="方向",
                label_en="Direction",
            )
        ],
        metrics=[
            TraceMetric(
                metric_id="objective",
                label_ja="目的関数",
                label_en="Objective",
                value=float(index),
                unit=None,
            )
        ],
        payload={} if payload is None else payload,
    )


def trace(*frames: TraceFrame, trace_id: str = "trace-a") -> AlgorithmTrace:
    return AlgorithmTrace(
        contract_version="1.0.0",
        dataset_version="0.2.0",
        data_version="1.0.0",
        trace_id=trace_id,
        method_id="M_EDUCATIONAL",
        profile_id="profile-educational",
        objective_id="objective-quadratic",
        scenario_id="scenario-dummy",
        generator_id="optimization-compass.educational-dummy",
        generator_version="1.0.0",
        implementation_mapping_status="not_applicable",
        implementation_id=None,
        objective={"family": "quadratic", "dimensions": 2},
        preset={"preset_id": "dummy"},
        parameters={"step_size": 0.25},
        initial_state={"point": [2.0, -1.0]},
        seed={"status": "not_applicable", "value": None},
        evaluation_budget=20,
        stopping={"max_evaluations": 20},
        environment={"runtime": "educational", "version": "1.0.0"},
        fairness_statement="同じ目的関数、初期値、評価予算を使う。",
        frames=list(frames),
        terminal_status="converged",
        terminal_summary_ja="デモを完了しました。",
        terminal_summary_en="The demo completed.",
        source_ids=["S001"],
    )


def test_contract_rejects_unknown_versions_fields_and_malformed_slugs() -> None:
    payload = trace(frame(0)).model_dump(mode="json")
    with pytest.raises(ValidationError, match="contract_version"):
        AlgorithmTrace.model_validate({**payload, "contract_version": "2.0.0"})
    with pytest.raises(ValidationError, match="extra_forbidden"):
        AlgorithmTrace.model_validate({**payload, "legacy_frames": []})
    with pytest.raises(ValidationError, match="event_type"):
        TraceFrame.model_validate({**payload["frames"][0], "event_type": "not a slug"})


def test_contract_versions_are_required_and_scalar_coercion_is_forbidden() -> None:
    payload = trace(frame(0)).model_dump(mode="json")
    without_version = dict(payload)
    without_version.pop("contract_version")
    with pytest.raises(ValidationError, match="contract_version"):
        AlgorithmTrace.model_validate(without_version)

    frame_payload = payload["frames"][0]
    with pytest.raises(ValidationError, match="frame_index"):
        TraceFrame.model_validate({**frame_payload, "frame_index": "0"})
    with pytest.raises(ValidationError, match="oracle_evaluations"):
        TraceFrame.model_validate({**frame_payload, "oracle_evaluations": True})
    with pytest.raises(ValidationError, match="coordinates"):
        TraceFrame.model_validate(
            {
                **frame_payload,
                "points": [{**frame_payload["points"][0], "coordinates": ["0.5", 1.5]}],
            }
        )
    with pytest.raises(ValidationError, match="contract_version"):
        TraceIndex.model_validate({})
    with pytest.raises(ValidationError, match="contract_version"):
        TraceBundle.model_validate({})


def test_frames_are_full_standalone_snapshots_with_unique_stable_ids() -> None:
    payload = frame(0).model_dump(mode="json")
    for field in ("points", "vectors", "metrics", "payload"):
        incomplete = dict(payload)
        incomplete.pop(field)
        with pytest.raises(ValidationError, match=field):
            TraceFrame.model_validate(incomplete)
    with pytest.raises(ValidationError, match="duplicate point"):
        TraceFrame.model_validate({**payload, "points": payload["points"] * 2})
    with pytest.raises(ValidationError, match="same dimension"):
        TraceFrame.model_validate(
            {
                **payload,
                "vectors": [{**payload["vectors"][0], "components": [1.0]}],
            }
        )


@pytest.mark.parametrize(
    "frames, message",
    [
        ([frame(1)], "contiguous"),
        ([frame(0), frame(2)], "contiguous"),
        ([frame(0, evaluations=2), frame(1, evaluations=1)], "oracle_evaluations"),
        (
            [
                frame(0).model_copy(update={"iteration": 1}),
                frame(1).model_copy(update={"iteration": 0}),
            ],
            "iteration",
        ),
        (
            [frame(0), frame(1).model_copy(update={"elapsed_time_ms": -1.0})],
            "elapsed_time_ms",
        ),
    ],
)
def test_trace_requires_contiguous_indices_and_monotonic_progress(
    frames: list[TraceFrame], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        trace(*frames)


@pytest.mark.parametrize(
    "replacement",
    [
        {"payload": {"bad": float("nan")}},
        {"payload": {"nested": [float("inf")]}},
        {"points": [{**frame(0).model_dump(mode="json")["points"][0], "value": float("-inf")}]},
    ],
)
def test_recursive_non_finite_numbers_are_rejected(replacement: dict[str, object]) -> None:
    payload = frame(0).model_dump(mode="json")
    with pytest.raises(ValidationError):
        TraceFrame.model_validate({**payload, **replacement})


def test_json_integer_values_are_limited_to_the_binary64_safe_range() -> None:
    payload = frame(0).model_dump(mode="json")
    with pytest.raises(ValidationError, match="safe binary64"):
        TraceFrame.model_validate({**payload, "payload": {"too_large": 2**53}})


def test_canonical_trace_bytes_are_deterministic_and_sorted() -> None:
    first = trace(frame(0, payload={"z": 1, "a": {"y": 2, "b": 3}}))
    second = trace(frame(0, payload={"a": {"b": 3, "y": 2}, "z": 1}))
    first_bytes = canonical_trace_bytes(first)
    assert first_bytes == canonical_trace_bytes(second)


def test_non_ascii_canonical_bytes_match_the_typescript_contract_fixture() -> None:
    fixture_path = Path(__file__).parents[1] / "site/src/contracts/trace.canonical.fixture.json"
    parsed = AlgorithmTrace.model_validate_json(fixture_path.read_bytes())
    canonical = canonical_trace_bytes(parsed)
    assert len(canonical) == 1868
    assert sha256(canonical).hexdigest() == (
        "ea01571779b5aee0f39ad791f1b2062d4ff5fed8660160fd7da4fe84b5bc4f8b"
    )


def test_frame_count_and_raw_canonical_size_limits_are_enforced() -> None:
    with pytest.raises(ValidationError, match="1,000"):
        trace(*(frame(index) for index in range(1001)))
    with pytest.raises(ValidationError, match="2 MiB"):
        trace(frame(0, payload={"text": "x" * (2 * 1024 * 1024)}))


def test_downsampling_is_deterministic_and_preserves_event_boundaries_and_keyframes() -> None:
    frames = [frame(index) for index in range(20)]
    frames[4] = frame(4, event_type="reflect")
    frames[5] = frame(5, event_type="iterate")
    frames[11] = frame(11, keyframe=True)
    first = downsample_frames(frames, 8)
    second = downsample_frames(frames, 8)
    assert [item.frame_index for item in first] == [item.frame_index for item in second]
    assert [item.frame_index for item in first] == list(range(8))
    assert {0, 4, 5, 11, 19} <= {item.iteration for item in first}
    assert [item.model_dump(exclude={"frame_index"}) for item in first] == [
        frames[item.iteration].model_dump(exclude={"frame_index"}) for item in first
    ]
    roundtrip = trace(*first)
    assert len(roundtrip.frames) == 8


def test_downsampling_fails_when_mandatory_frames_exceed_capacity() -> None:
    frames = [frame(index, keyframe=True) for index in range(6)]
    with pytest.raises(ValueError, match="mandatory"):
        downsample_frames(frames, 5)


def test_educational_and_supported_implementation_mapping_semantics() -> None:
    payload = trace(frame(0)).model_dump(mode="json")
    with pytest.raises(ValidationError, match="not_applicable"):
        AlgorithmTrace.model_validate({**payload, "implementation_id": "I_SCIP"})
    with pytest.raises(ValidationError, match="supported"):
        AlgorithmTrace.model_validate(
            {
                **payload,
                "implementation_mapping_status": "supported",
                "implementation_id": None,
            }
        )


def test_bundle_rejects_reference_and_fairness_mismatches() -> None:
    member = trace(frame(0, evaluations=0), frame(1, evaluations=2))
    base = dict(
        contract_version="1.0.0",
        bundle_id="bundle-a",
        comparison_id="comparison-a",
        dataset_version="0.2.0",
        data_version="1.0.0",
        objective_id=member.objective_id,
        objective=member.objective,
        initial_state=member.initial_state,
        seed=member.seed,
        evaluation_budget=member.evaluation_budget,
        stopping=member.stopping,
        environment=member.environment,
        fairness_statement=member.fairness_statement,
        member_traces=[member],
        synchronization="oracle_evaluations",
    )
    TraceBundle(**base)
    with pytest.raises(ValidationError, match="objective"):
        TraceBundle(**{**base, "objective": {"family": "rosenbrock"}})
    with pytest.raises(ValidationError, match="fairness_statement"):
        TraceBundle(**{**base, "fairness_statement": "different"})


def test_bundle_synchronizes_members_by_cumulative_evaluations_not_frame_index() -> None:
    first = trace(
        frame(0, evaluations=0),
        frame(1, evaluations=3),
        frame(2, evaluations=7),
        trace_id="first",
    )
    second = trace(
        frame(0, evaluations=0),
        frame(1, evaluations=1),
        frame(2, evaluations=5),
        trace_id="second",
    )
    bundle = TraceBundle(
        contract_version="1.0.0",
        bundle_id="bundle-a",
        comparison_id="comparison-a",
        dataset_version="0.2.0",
        data_version="1.0.0",
        objective_id=first.objective_id,
        objective=first.objective,
        initial_state=first.initial_state,
        seed=first.seed,
        evaluation_budget=first.evaluation_budget,
        stopping=first.stopping,
        environment=first.environment,
        fairness_statement=first.fairness_statement,
        member_traces=[first, second],
        synchronization="oracle_evaluations",
    )
    synchronized = synchronize_bundle(bundle, 5)
    assert {key: value.frame_index for key, value in synchronized.items()} == {
        "first": 1,
        "second": 2,
    }


def test_bundle_sync_has_no_future_snapshot_before_a_members_first_evaluation() -> None:
    member = trace(
        frame(0, evaluations=3),
        frame(1, evaluations=5),
        trace_id="delayed",
    )
    bundle = TraceBundle(
        contract_version="1.0.0",
        bundle_id="bundle-delayed",
        comparison_id="comparison-a",
        dataset_version=member.dataset_version,
        data_version=member.data_version,
        objective_id=member.objective_id,
        objective=member.objective,
        initial_state=member.initial_state,
        seed=member.seed,
        evaluation_budget=member.evaluation_budget,
        stopping=member.stopping,
        environment=member.environment,
        fairness_statement=member.fairness_statement,
        member_traces=[member],
        synchronization="oracle_evaluations",
    )
    assert synchronize_bundle(bundle, 2) == {"delayed": None}
    assert synchronize_bundle(bundle, 3)["delayed"] == member.frames[0]
