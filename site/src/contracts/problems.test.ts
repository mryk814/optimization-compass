import { describe, expect, test } from "vitest";

import { parseProblemCatalog } from "./problems";

const definition = {
  problem_definition_id: "P", name_ja: "問題", name_en: "Problem", mathematical_family: "quadratic",
  variable_domain: "continuous", objective_form: "quadratic", objective_direction: "minimize",
  available_oracles: ["objective_value"], constraint_class: "none", dimensionality_policy: { kind: "fixed", dimension: 2 },
  known_reference_semantics: "Exact", related_problem_ids: ["PA006"], feature_ids: ["F_OBJECTIVE_QUADRATIC"],
  source_ids: ["S055"], last_verified: "2026-07-15",
};
const instance = {
  problem_instance_id: "I", problem_definition_id: "P", name_ja: "例", name_en: "Example", registry_key: "problem.example.v1",
  dimension: 2, parameters: { weights: [1, 1] }, bounds: { x: [-1, 1], y: [-1, 1] }, constraints: [],
  initialization_candidates: [{ candidate_id: "default", point: [1, 1] }], seed_status: "not_applicable", seed_value: null,
  known_reference_status: "known_exact", known_reference: { point: [0, 0], value: 0, source_ids: ["S055"] },
  display: { range: { x: [-1, 1], y: [-1, 1], z: [0, 2] }, expression: "x²+y²" }, intended_phenomena: ["curvature"],
  limitations_ja: "教材", limitations_en: "Lesson", source_ids: ["S055"], last_verified: "2026-07-15",
};

describe("ProblemCatalog parser", () => {
  test("parses a closed definition-instance catalog", () => {
    const catalog = parseProblemCatalog({ contract_version: "1.0.0", dataset_version: "0.5.0", definitions: [definition], instances: [instance] });
    expect(catalog.instances[0].known_reference_status).toBe("known_exact");
  });

  test("rejects unresolved definitions and inconsistent references", () => {
    expect(() => parseProblemCatalog({ contract_version: "1.0.0", dataset_version: "0.5.0", definitions: [definition], instances: [{ ...instance, problem_definition_id: "missing" }] })).toThrow(/Unknown problem definition/u);
    expect(() => parseProblemCatalog({ contract_version: "1.0.0", dataset_version: "0.5.0", definitions: [definition], instances: [{ ...instance, known_reference: null }] })).toThrow(/known reference/u);
  });
});
