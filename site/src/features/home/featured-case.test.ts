import { describe, expect, test } from "vitest";

import { parseGalleryIndex, type GalleryIndex } from "../../contracts/gallery";
import {
  parseLearningJourneyIndex,
  type LearningJourneyIndex,
} from "../../contracts/learning-journeys";
import rawGallery from "../../../public/data/gallery.json";
import rawLearningJourneys from "../../../public/data/learning-journeys.json";
import { selectFeaturedCase } from "./featured-case";

const gallery = {
  contract_version: "2.0.0",
  dataset_version: "test",
  cases: [
    galleryCase("first-in-gallery"),
    galleryCase("near-complete"),
    galleryCase("complete"),
  ],
} as GalleryIndex;

describe("featured Home case", () => {
  test("selects the first complete journey from current release data", () => {
    const featured = selectFeaturedCase(
      parseGalleryIndex(rawGallery),
      parseLearningJourneyIndex(rawLearningJourneys),
    );

    expect(featured).toMatchObject({
      canonicalUrl: "/gallery/EC013",
      item: { case_id: "EC013" },
    });
  });

  test("prefers a complete canonical journey over Gallery order", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "partial", 1),
      journey("complete", "complete", 0),
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys)).toMatchObject({
      canonicalUrl: "/gallery/complete",
      item: { case_id: "complete" },
    });
  });

  test("uses missing dimensions then stable identity for partial journeys", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "partial", 4),
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys)).toMatchObject({
      canonicalUrl: "/gallery/near-complete",
      item: { case_id: "near-complete" },
    });
  });

  test("skips a partial journey without both Theater and Compare routes", () => {
    const journeys = journeyIndex([
      journey("first-in-gallery", "partial", 0, false),
      journey("near-complete", "partial", 1),
    ]);

    expect(selectFeaturedCase(gallery, journeys)).toMatchObject({
      canonicalUrl: "/gallery/near-complete",
      item: { case_id: "near-complete" },
    });
  });

  test("rejects mismatched generated releases", () => {
    expect(() => selectFeaturedCase(
      gallery,
      { ...journeyIndex([]), dataset_version: "other" },
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
      scenarios: hasCompleteRoute ? [{ role: "primary" }] : [],
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
