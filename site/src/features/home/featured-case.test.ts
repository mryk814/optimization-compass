import { describe, expect, test } from "vitest";

import { parseGalleryIndex, type GalleryIndex } from "../../contracts/gallery";
import {
  parseLearningJourneyIndex,
  type LearningJourneyIndex,
} from "../../contracts/learning-journeys";
import { parseProblemCatalog, type ProblemCatalog } from "../../contracts/problems";
import rawGallery from "../../../public/data/gallery.json";
import rawLearningJourneys from "../../../public/data/learning-journeys.json";
import rawProblems from "../../../public/data/problems.json";
import { selectFeaturedCase } from "./featured-case";

const caseIds = ["first-in-gallery", "near-complete", "complete"];
const gallery = {
  contract_version: "2.0.0",
  dataset_version: "test",
  cases: caseIds.map(galleryCase),
} as GalleryIndex;
const problems = problemCatalog(caseIds);

describe("featured Home case", () => {
  test("selects the highest-ranked complete journey and problem from current release data", () => {
    const featured = selectFeaturedCase(
      parseGalleryIndex(rawGallery),
      parseLearningJourneyIndex(rawLearningJourneys),
      parseProblemCatalog(rawProblems),
    );

    expect(featured).toMatchObject({
      canonicalUrl: "/gallery/EC017",
      formulation: {
        sense: "objectives",
        variables: "(x, y) ∈ ℝ²",
      },
      item: { case_id: "EC017" },
      problemDefinition: { problem_definition_id: "PROBLEM_BIOBJECTIVE_CONTINUOUS" },
      problemInstance: { problem_instance_id: "INSTANCE_BIOBJECTIVE_QUADRATIC_2D" },
    });
  });

  test("prefers a complete canonical journey over Gallery order", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "partial", 1),
      journey("complete", "complete", 0),
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys, problems)).toMatchObject({
      canonicalUrl: "/gallery/complete",
      item: { case_id: "complete" },
      problemInstance: { problem_instance_id: "INSTANCE_complete" },
    });
  });

  test("uses missing dimensions then stable identity for partial journeys", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "partial", 4),
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys, problems)).toMatchObject({
      canonicalUrl: "/gallery/near-complete",
      item: { case_id: "near-complete" },
    });
  });

  test("skips a partial journey without both Theater and Compare routes", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "partial", 0, false),
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys, problems)).toMatchObject({
      canonicalUrl: "/gallery/near-complete",
      item: { case_id: "near-complete" },
    });
  });

  test("skips a journey whose canonical problem instance is unavailable", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "complete", 0),
      journey("near-complete", "partial", 1),
    ]);
    const incompleteProblems = problemCatalog(["near-complete"]);

    expect(selectFeaturedCase(gallery, journeys, incompleteProblems)).toMatchObject({
      item: { case_id: "near-complete" },
    });
  });

  test("skips the highest-ranked journey when its problem shape is not truthfully formattable", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "complete", 0),
      journey("near-complete", "partial", 1),
    ]);
    const unsupportedProblems = problemCatalog(["first-in-gallery", "near-complete"]);
    unsupportedProblems.instances[0].bounds = {
      lower: [-1, -1],
      upper: [1, 1],
    };

    expect(selectFeaturedCase(gallery, journeys, unsupportedProblems)).toMatchObject({
      item: { case_id: "near-complete" },
      problemInstance: { problem_instance_id: "INSTANCE_near-complete" },
    });
  });

  test("skips a journey whose scenario definition disagrees with its instance", () => {
    const first = journey("first-in-gallery", "complete", 0);
    first.journey.scenarios[0].problem_definition_id = "PROBLEM_OTHER";
    const journeys = journeyIndex([
      first,
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys, problems)).toMatchObject({
      item: { case_id: "near-complete" },
    });
  });

  test("rejects mismatched generated releases", () => {
    expect(() => selectFeaturedCase(
      gallery,
      { ...journeyIndex([]), dataset_version: "other" },
      problems,
    )).toThrow(/dataset versions do not match/u);
  });
});

function galleryCase(caseId: string) {
  return {
    case_id: caseId,
    status: "published",
    candidate_methods: [{ method_id: "M_CANDIDATE", reason: "候補理由" }],
    excluded_methods: [{ method_id: "M_EXCLUDED", reason: "除外理由" }],
  } as GalleryIndex["cases"][number];
}

function journey(
  journeyId: string,
  status: "complete" | "partial",
  missingDimensionCount: number,
  hasCompleteRoute = true,
) {
  return {
    journey: {
      journey_id: journeyId,
      case_id: journeyId,
      canonical_url: `/gallery/${journeyId}`,
      status,
      scenarios: hasCompleteRoute ? [{
        role: "primary",
        problem_definition_id: "PROBLEM_TEST",
        problem_instance_id: `INSTANCE_${journeyId}`,
      }] : [],
      comparisons: hasCompleteRoute ? [{ comparison_id: "COMPARE" }] : [],
    },
    assessment: {
      journey_id: journeyId,
      status,
      missing_dimensions: Array.from(
        { length: missingDimensionCount },
        () => "primary_scenario",
      ),
    },
  };
}

function journeyIndex(rows: ReturnType<typeof journey>[]): LearningJourneyIndex {
  return {
    dataset_version: "test",
    journeys: rows.map((row) => row.journey),
    assessments: rows.map((row) => row.assessment),
  } as LearningJourneyIndex;
}

function problemCatalog(ids: string[]): ProblemCatalog {
  return {
    contract_version: "1.0.0",
    dataset_version: "test",
    definitions: [{
      problem_definition_id: "PROBLEM_TEST",
      name_ja: "テスト問題",
      name_en: "Test problem",
      mathematical_family: "quadratic",
      variable_domain: "continuous",
      objective_form: "quadratic",
      objective_direction: "minimize",
      available_oracles: ["objective_value"],
      constraint_class: "bounds",
      dimensionality_policy: { kind: "fixed", dimension: 2 },
      known_reference_semantics: "No reference is needed for selection tests.",
      related_problem_ids: [],
      feature_ids: ["F_TEST"],
      source_ids: ["S_TEST"],
      last_verified: "2026-07-17",
    }],
    instances: ids.map((caseId) => ({
      problem_instance_id: `INSTANCE_${caseId}`,
      problem_definition_id: "PROBLEM_TEST",
      name_ja: `テストinstance ${caseId}`,
      name_en: `Test instance ${caseId}`,
      registry_key: `problem.test.${caseId}`,
      dimension: 2,
      parameters: {},
      bounds: { x: [-1, 1], y: [-1, 1] },
      constraints: [],
      initialization_candidates: [{ candidate_id: "default", point: [0, 0] }],
      seed_status: "not_applicable",
      seed_value: null,
      known_reference_status: "unknown",
      known_reference: null,
      display: { axis_labels: ["x", "y"], expression: "min x²+y²" },
      intended_phenomena: ["selection_test"],
      limitations_ja: "featured Case選択用のテストfixtureです。",
      limitations_en: "A fixture for featured Case selection.",
      source_ids: ["S_TEST"],
      last_verified: "2026-07-17",
    })),
  };
}
