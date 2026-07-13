import { describe, expect, test } from "vitest";

import {
  AtlasStateUrlTooLongError,
  decodeAtlasState,
  encodeAtlasState,
  toRecommendationAnswers,
  type AtlasCompatibilityCatalog,
  type AtlasStateV1,
} from "./atlas-state";

const catalog: AtlasCompatibilityCatalog = {
  datasetVersion: "2026-07-14",
  viewId: "problem-structure",
  viewVersion: "1.2.0",
  nodeIds: new Set(["root", "連続最適化"]),
  questions: {
    objective: {
      answerType: "single_choice",
      allowedAnswers: ["single", "multi", "unknown"],
    },
    constraints: {
      answerType: "multi_choice",
      allowedAnswers: ["linear", "nonlinear", "black_box"],
    },
    landscape: {
      answerType: "single_choice",
      allowedAnswers: ["smooth", "non_smooth"],
    },
  },
};

function encodeRawText(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function encodeRawJson(value: unknown): string {
  return encodeRawText(JSON.stringify(value));
}

function decodeRawJson(token: string): unknown {
  const base64 = token.replaceAll("-", "+").replaceAll("_", "/");
  const binary = atob(base64 + "=".repeat((4 - (base64.length % 4)) % 4));
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes)) as unknown;
}

function validRawState(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    stateVersion: 1,
    datasetVersion: catalog.datasetVersion,
    viewId: catalog.viewId,
    viewVersion: catalog.viewVersion,
    answers: {},
    ...overrides,
  };
}

describe("AtlasState URL codec", () => {
  test("round-trips canonical state with Japanese UTF-8 IDs", () => {
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      selectedNodeId: "連続最適化",
      answers: {
        objective: { status: "answered", values: ["single"] },
      },
    };

    const token = encodeAtlasState(state);
    const decoded = decodeAtlasState(token, catalog);

    expect(token).toMatch(/^[A-Za-z0-9_-]+$/u);
    expect(token).not.toContain("=");
    expect(decoded).toEqual({ state, warnings: [] });
  });

  test("sorts question IDs and multi-choice values without mutating input", () => {
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      answers: {
        objective: { status: "answered", values: ["single"] },
        constraints: { status: "answered", values: ["nonlinear", "linear"] },
      },
    };
    const sameStateWithDifferentInsertionOrder: AtlasStateV1 = {
      ...state,
      answers: {
        constraints: { status: "answered", values: ["linear", "nonlinear"] },
        objective: { status: "answered", values: ["single"] },
      },
    };
    const before = structuredClone(state);

    const token = encodeAtlasState(state);

    expect(encodeAtlasState(sameStateWithDifferentInsertionOrder)).toBe(token);
    expect(state).toEqual(before);
    expect(decodeRawJson(token)).toEqual({
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      answers: {
        constraints: { status: "answered", values: ["linear", "nonlinear"] },
        objective: { status: "answered", values: ["single"] },
      },
    });
  });

  test("keeps unknown, unanswered, and not-applicable as distinct states", () => {
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      answers: {
        objective: { status: "unknown", values: ["unknown"] },
        constraints: { status: "not_applicable", values: [] },
      },
    };

    const decoded = decodeAtlasState(encodeAtlasState(state), catalog).state;

    expect(decoded.answers.objective).toEqual({ status: "unknown", values: ["unknown"] });
    expect(decoded.answers.constraints).toEqual({ status: "not_applicable", values: [] });
    expect(decoded.answers.landscape).toBeUndefined();
    expect(decodeRawJson(encodeAtlasState(state))).not.toHaveProperty(
      "answers.landscape.status",
      "unanswered",
    );
  });

  test("projects answered and unknown values while omitting unanswered and not-applicable", () => {
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      answers: {
        objective: { status: "unknown", values: ["unknown"] },
        constraints: { status: "answered", values: ["linear", "nonlinear"] },
        landscape: { status: "not_applicable", values: [] },
      },
    };
    const before = structuredClone(state);

    expect(toRecommendationAnswers(state)).toEqual({
      constraints: ["linear", "nonlinear"],
      objective: ["unknown"],
    });
    expect(state).toEqual(before);
  });

  test.each([
    ["empty token", ""],
    ["invalid base64url", "not+base64"],
    ["invalid JSON", encodeRawText("{")],
  ])("rejects malformed input: %s", (_label, token) => {
    expect(() => decodeAtlasState(token, catalog)).toThrow(/AtlasState/u);
  });

  test("rejects unknown state versions", () => {
    const token = encodeRawJson(validRawState({ stateVersion: 2 }));

    expect(() => decodeAtlasState(token, catalog)).toThrow(/stateVersion.*2/u);
  });

  test.each([
    ["datasetVersion", validRawState({ datasetVersion: undefined })],
    ["viewId", validRawState({ viewId: undefined })],
    ["viewVersion", validRawState({ viewVersion: undefined })],
    ["answers", validRawState({ answers: undefined })],
  ])("rejects missing required metadata: %s", (_label, rawState) => {
    expect(() => decodeAtlasState(encodeRawJson(rawState), catalog)).toThrow();
  });

  test.each([
    ["empty dataset ID", validRawState({ datasetVersion: "" })],
    ["blank view ID", validRawState({ viewId: "   " })],
    ["empty view version", validRawState({ viewVersion: "" })],
    [
      "empty question ID",
      validRawState({ answers: { "": { status: "answered", values: ["single"] } } }),
    ],
    [
      "empty answer ID",
      validRawState({ answers: { objective: { status: "answered", values: [""] } } }),
    ],
  ])("rejects empty IDs: %s", (_label, rawState) => {
    expect(() => decodeAtlasState(encodeRawJson(rawState), catalog)).toThrow(/empty|空/u);
  });

  test.each([
    ["duplicate single-choice value", ["single", "single"], /single_choice/u],
    ["multiple single-choice values", ["single", "multi"], /single_choice/u],
  ])("rejects %s", (_label, values, expectedError) => {
    const token = encodeRawJson(
      validRawState({ answers: { objective: { status: "answered", values } } }),
    );

    expect(() => decodeAtlasState(token, catalog)).toThrow(expectedError);
  });

  test.each([
    ["answered without a value", { status: "answered", values: [] }],
    ["answered with unknown sentinel", { status: "answered", values: ["unknown"] }],
    ["unknown without sentinel", { status: "unknown", values: [] }],
    ["unknown with extra value", { status: "unknown", values: ["unknown", "single"] }],
    ["not-applicable with a value", { status: "not_applicable", values: ["single"] }],
    ["explicit unanswered", { status: "unanswered", values: [] }],
  ])("rejects invalid status/value combination: %s", (_label, answer) => {
    const token = encodeRawJson(validRawState({ answers: { objective: answer } }));

    expect(() => decodeAtlasState(token, catalog)).toThrow(/status|values/u);
  });

  test("migrates stale dataset and view versions with Japanese warnings", () => {
    const token = encodeRawJson(
      validRawState({
        datasetVersion: "2025-01-01",
        viewVersion: "1.0.0",
        answers: { objective: { status: "answered", values: ["single"] } },
      }),
    );

    const decoded = decodeAtlasState(token, catalog);

    expect(decoded.state.datasetVersion).toBe(catalog.datasetVersion);
    expect(decoded.state.viewVersion).toBe(catalog.viewVersion);
    expect(decoded.state.answers.objective).toEqual({ status: "answered", values: ["single"] });
    expect(decoded.warnings).toHaveLength(2);
    expect(decoded.warnings[0]).toMatch(/データセット/u);
    expect(decoded.warnings[1]).toMatch(/ビュー/u);
  });

  test("removes invalid questions, answer values, and selected nodes with warnings", () => {
    const token = encodeRawJson(
      validRawState({
        selectedNodeId: "deleted-node",
        answers: {
          deleted_question: { status: "answered", values: ["single"] },
          constraints: { status: "answered", values: ["black_box", "invalid", "linear"] },
          landscape: { status: "answered", values: ["deleted-answer"] },
          objective: { status: "unknown", values: ["unknown"] },
        },
      }),
    );

    const decoded = decodeAtlasState(token, catalog);

    expect(decoded.state).not.toHaveProperty("selectedNodeId");
    expect(decoded.state.answers).toEqual({
      constraints: { status: "answered", values: ["black_box", "linear"] },
      objective: { status: "unknown", values: ["unknown"] },
    });
    expect(decoded.warnings.some((warning) => warning.includes("deleted-node"))).toBe(true);
    expect(decoded.warnings.some((warning) => warning.includes("deleted_question"))).toBe(true);
    expect(decoded.warnings.some((warning) => warning.includes("invalid"))).toBe(true);
    expect(decoded.warnings.some((warning) => warning.includes("deleted-answer"))).toBe(true);
  });

  test("removes unknown status when the current catalog has no canonical unknown answer", () => {
    const token = encodeRawJson(
      validRawState({
        answers: { landscape: { status: "unknown", values: ["unknown"] } },
      }),
    );

    const decoded = decodeAtlasState(token, catalog);

    expect(decoded.state.answers.landscape).toBeUndefined();
    expect(decoded.warnings).toEqual([
      "質問「landscape」の回答「unknown」は現在の選択肢にないため除外しました。",
    ]);
    expect(toRecommendationAnswers(decoded.state)).toEqual({});
  });

  test("throws a named error instead of truncating tokens longer than 1800 characters", () => {
    const answers = Object.fromEntries(
      Array.from({ length: 80 }, (_, index) => [
        `question-${index.toString().padStart(3, "0")}`,
        { status: "answered" as const, values: [`${"value".repeat(8)}-${index}`] },
      ]),
    );
    const state: AtlasStateV1 = {
      stateVersion: 1,
      datasetVersion: catalog.datasetVersion,
      viewId: catalog.viewId,
      viewVersion: catalog.viewVersion,
      answers,
    };

    expect(() => encodeAtlasState(state)).toThrow(AtlasStateUrlTooLongError);
    expect(() => encodeAtlasState(state)).toThrow(/1800/u);
    try {
      encodeAtlasState(state);
    } catch (error) {
      expect(error).toHaveProperty("name", "AtlasStateUrlTooLongError");
    }
  });

  test("rejects an incoming over-limit URL token before decoding it", () => {
    expect(() => decodeAtlasState("a".repeat(1801), catalog)).toThrow(
      AtlasStateUrlTooLongError,
    );
  });
});
