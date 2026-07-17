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
  test("selects the complete constrained-design journey and problem from current release data", () => {
    const featured = selectFeaturedCase(
      parseGalleryIndex(rawGallery),
      parseLearningJourneyIndex(rawLearningJourneys),
      parseProblemCatalog(rawProblems),
    );

    expect(featured).toMatchObject({
      canonicalUrl: "/gallery/constrained-design",
      item: { case_id: "constrained-design" },
      problemDefinition: { problem_definition_id: "PROBLEM_CONSTRAINED_CONTINUOUS_2D" },
      problemInstance: { problem_instance_id: "INSTANCE_CONSTRAINED_DISK_2D" },
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
      variable_domain: "continuous",
      objective_direction: "minimize",
    }],
    instances: ids.map((caseId) => ({
      problem_instance_id: `INSTANCE_${caseId}`,
      problem_definition_id: "PROBLEM_TEST",
      dimension: 2,
      bounds: { x: [-1, 1], y: [-1, 1] },
      constraints: [],
      display: { axis_labels: ["x", "y"], expression: "min x²+y²" },
    })),
  } as ProblemCatalog;
}
