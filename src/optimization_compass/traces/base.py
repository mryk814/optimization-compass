from __future__ import annotations

from bisect import bisect_right
from collections.abc import Sequence

from optimization_compass.trace_models import TraceBundle, TraceFrame


def downsample_frames(frames: Sequence[TraceFrame], limit: int) -> list[TraceFrame]:
    """Select frames deterministically without interpolating or changing snapshots.

    First/last frames, explicit keyframes, and the first frame of every event-type segment are
    mandatory. Remaining capacity is spread over the other frames using equal-width bins.
    """
    if limit < 1:
        raise ValueError("downsampling limit must be at least one")
    if len(frames) <= limit:
        return list(frames)

    mandatory = {0, len(frames) - 1}
    mandatory.update(index for index, frame in enumerate(frames) if frame.keyframe)
    mandatory.update(
        index
        for index in range(1, len(frames))
        if frames[index].event_type != frames[index - 1].event_type
    )
    if len(mandatory) > limit:
        raise ValueError("mandatory event/key frames exceed the requested downsampling capacity")

    candidates = [index for index in range(len(frames)) if index not in mandatory]
    remaining = limit - len(mandatory)
    selected = set(mandatory)
    if remaining:
        candidate_count = len(candidates)
        selected.update(
            candidates[((2 * slot + 1) * candidate_count) // (2 * remaining)]
            for slot in range(remaining)
        )
    return [frames[index] for index in sorted(selected)]


def synchronize_bundle(bundle: TraceBundle, oracle_evaluations: int) -> dict[str, TraceFrame]:
    """Return each member's latest snapshot at a cumulative evaluation position."""
    if oracle_evaluations < 0:
        raise ValueError("oracle_evaluations must be non-negative")
    synchronized: dict[str, TraceFrame] = {}
    for trace in bundle.member_traces:
        values = [frame.oracle_evaluations for frame in trace.frames]
        index = max(0, bisect_right(values, oracle_evaluations) - 1)
        synchronized[trace.trace_id] = trace.frames[index]
    return synchronized
