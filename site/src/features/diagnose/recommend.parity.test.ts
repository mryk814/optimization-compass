/// <reference types="node" />

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, test } from "vitest";

import { parseSiteData } from "../../contracts/site-data";
import { recommend, type EntityRecommendation, type RecommendationResult } from "./recommend";

type Projection = Record<string, unknown>;
type Fixture = {
  dataset_version: string;
  cases: Array<{
    case_id: string;
    request: { answers: Record<string, string[]>; language?: "ja" | "en" };
    expected: Projection;
  }>;
};

function entities(items: EntityRecommendation[]) {
  return items.map((item) => ({ entity_id: item.entity_id, source_ids: item.source_ids }));
}
function project(result: RecommendationResult): Projection {
  return {
    alternatives_first: entities(result.alternatives_first),
    first_choices: entities(result.first_choices),
    conditional_choices: entities(result.conditional_choices),
    excluded_methods: entities(result.excluded_methods),
    candidate_problem_archetypes: entities(result.candidate_problem_archetypes),
    followups: result.followups.map(({ question_id, target_type, target_ids }) => ({
      question_id,
      target_type,
      target_ids,
    })),
    warnings: result.warnings,
    trace: result.trace.map(({ rule_id, source_ids }) => ({ rule_id, source_ids })),
  };
}

const explicitlyRequested = process.env.RUN_RECOMMENDATION_PARITY === "1";
const parityDescribe = explicitlyRequested ? describe : describe.skip;

parityDescribe("live Python/TypeScript recommendation parity", () => {
  test("matches all shared fixtures against Python and committed expectations", () => {
    const repositoryRoot = resolve(process.cwd(), "..");
    const fixturePath = resolve(repositoryRoot, "tests/fixtures/recommendation_cases.json");
    const fixture = JSON.parse(readFileSync(fixturePath, "utf-8")) as Fixture;
    const rawData = JSON.parse(
      readFileSync(resolve(process.cwd(), "public/data/recommendation/site-data.json"), "utf-8"),
    ) as unknown;
    const data = parseSiteData(rawData, fixture.dataset_version);
    const uv = process.platform === "win32" ? "uv.exe" : "uv";
    const python = JSON.parse(
      execFileSync(
        uv,
        ["run", "python", "scripts/recommendation_parity.py", fixturePath],
        {
          cwd: repositoryRoot,
          encoding: "utf-8",
          env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" },
        },
      ),
    ) as Array<{ case_id: string; result: Projection }>;
    const pythonById = new Map(python.map((item) => [item.case_id, item.result]));

    expect(fixture.cases).toHaveLength(9);
    fixture.cases.forEach((item) => {
      const browser = project(
        recommend(data, item.request.answers, { language: item.request.language ?? "ja" }),
      );
      expect(browser, `${item.case_id}: browser vs Python`).toEqual(pythonById.get(item.case_id));
      expect(browser, `${item.case_id}: browser vs expected`).toEqual(item.expected);
    });
  });
});
