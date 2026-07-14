import { describe, expect, test } from "vitest";

import {
  parseAlgorithmTrace,
  parseTraceIndex,
  parseTraceBundle,
  canonicalTraceBytes,
  synchronizeTraceBundle,
  traceEventExplanation,
  traceEventLabel,
} from "./trace";
import {
  algorithmTraceFixture as payload,
  traceFrameFixture as frame,
} from "./trace.fixtures";
import canonicalFixture from "./trace.canonical.fixture.json";

describe("AlgorithmTrace parser", () => {
  test("accepts unknown event types and gives them a readable fallback label", () => {
    const parsed = parseAlgorithmTrace(payload);
    expect(parsed.frames[0].event_type).toBe("future-event");
    expect(traceEventLabel(parsed.frames[0], "ja")).toBe("未定義イベント（future-event）");
    expect(traceEventLabel(parsed.frames[0], "en")).toBe("Unknown event (future-event)");
  });

  test("rejects unknown versions and exact-core-key violations", () => {
    expect(() => parseAlgorithmTrace({ ...payload, contract_version: "2.0.0" })).toThrow(
      /version/i,
    );
    expect(() => parseAlgorithmTrace({ ...payload, legacy_frames: [] })).toThrow(/unknown/i);
    expect(() =>
      parseAlgorithmTrace({ ...payload, frames: [{ ...frame, legacy_point: [] }] }),
    ).toThrow(/unknown/i);
    const withoutVersion = { ...payload } as Record<string, unknown>;
    delete withoutVersion.contract_version;
    expect(() => parseAlgorithmTrace(withoutVersion)).toThrow(/contract_version/u);
  });

  test("rejects malformed slugs, non-finite JSON, and broken frame progression", () => {
    expect(() =>
      parseAlgorithmTrace({ ...payload, frames: [{ ...frame, event_type: "not a slug" }] }),
    ).toThrow(/event_type/i);
    expect(() =>
      parseAlgorithmTrace({ ...payload, frames: [{ ...frame, payload: { bad: Infinity } }] }),
    ).toThrow(/finite/i);
    expect(() =>
      parseAlgorithmTrace({
        ...payload,
        frames: [frame, { ...frame, frame_index: 2, iteration: 1, oracle_evaluations: 1 }],
      }),
    ).toThrow(/contiguous/i);
    expect(() =>
      parseAlgorithmTrace({ ...payload, frames: [{ ...frame, frame_index: "0" }] }),
    ).toThrow(/frame_index/u);
    expect(() =>
      parseAlgorithmTrace({ ...payload, frames: [{ ...frame, oracle_evaluations: true }] }),
    ).toThrow(/oracle_evaluations/u);
  });

  test("canonical bytes use Python-compatible Unicode code-point key ordering", () => {
    const parsed = parseAlgorithmTrace(canonicalFixture);
    const canonical = new TextDecoder().decode(canonicalTraceBytes(parsed));
    expect(canonical).toContain('"あ":"hiragana","":"private","😀":"astral"');
    expect(canonicalTraceBytes(parsed).byteLength).toBe(1096);
  });

  test("unknown explanation keys use a deterministic common fallback", () => {
    const parsed = parseAlgorithmTrace(payload);
    expect(traceEventExplanation(parsed.frames[0], "ja")).toBe(
      "説明は未登録です（trace.future-event）",
    );
  });
});

describe("TraceBundle parser", () => {
  const member = { ...payload, frames: [frame, { ...frame, frame_index: 1, iteration: 1, oracle_evaluations: 3 }] };
  const bundle = {
    contract_version: "1.0.0",
    bundle_id: "bundle-a",
    comparison_id: "comparison-a",
    dataset_version: payload.dataset_version,
    data_version: payload.data_version,
    objective_id: payload.objective_id,
    objective: payload.objective,
    initial_state: payload.initial_state,
    seed: payload.seed,
    evaluation_budget: payload.evaluation_budget,
    stopping: payload.stopping,
    environment: payload.environment,
    fairness_statement: payload.fairness_statement,
    member_traces: [member],
    synchronization: "oracle_evaluations",
  };

  test("enforces exact shared fairness fields", () => {
    expect(parseTraceBundle(bundle).member_traces).toHaveLength(1);
    expect(() => parseTraceBundle({ ...bundle, fairness_statement: "different" })).toThrow(
      /fairness_statement/u,
    );
    expect(() => parseTraceBundle({ ...bundle, frame_sync: true })).toThrow(/unknown/u);
    const withoutVersion = { ...bundle } as Record<string, unknown>;
    delete withoutVersion.contract_version;
    expect(() => parseTraceBundle(withoutVersion)).toThrow(/contract_version/u);
  });

  test("synchronizes cumulative evaluations rather than frame indexes", () => {
    const second = {
      ...member,
      trace_id: "trace-b",
      frames: [frame, { ...frame, frame_index: 1, iteration: 1, oracle_evaluations: 2 }],
    };
    const parsed = parseTraceBundle({ ...bundle, member_traces: [member, second] });
    expect(Object.fromEntries(
      Object.entries(synchronizeTraceBundle(parsed, 2)).map(([key, value]) => [key, value?.frame_index]),
    )).toEqual({ "dummy-educational": 0, "trace-b": 1 });
  });

  test("returns null before a member has any snapshot", () => {
    const delayed = {
      ...member,
      frames: [
        { ...frame, oracle_evaluations: 3 },
        { ...frame, frame_index: 1, iteration: 1, oracle_evaluations: 5 },
      ],
    };
    const parsed = parseTraceBundle({ ...bundle, member_traces: [delayed] });
    expect(synchronizeTraceBundle(parsed, 2)).toEqual({ "dummy-educational": null });
  });
});

test("TraceIndex rejects paths that can escape the published trace directory", () => {
  const index = {
    contract_version: "1.0.0",
    dataset_version: "0.2.0",
    data_version: "1.0.0",
    traces: [{
      trace_id: "trace-a",
      path: "https://example.invalid/trace.json",
      method_id: "M_A",
      profile_id: "PROFILE_A",
      objective_id: "OBJECTIVE_A",
      scenario_id: "SCENARIO_A",
      title_ja: "デモ",
      title_en: "Demo",
    }],
  };
  expect(() => parseTraceIndex(index)).toThrow(/safe relative/u);
});

test("TraceIndex requires its version and at least one trace", () => {
  expect(() => parseTraceIndex({
    dataset_version: "0.2.0",
    data_version: "1.0.0",
    traces: [],
  })).toThrow(/contract_version/u);
  expect(() => parseTraceIndex({
    contract_version: "1.0.0",
    dataset_version: "0.2.0",
    data_version: "1.0.0",
    traces: [],
  })).toThrow(/trace/u);
});
