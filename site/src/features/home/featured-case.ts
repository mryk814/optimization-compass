import type { GalleryCase, GalleryIndex } from "../../contracts/gallery";
import type { LearningJourneyIndex } from "../../contracts/learning-journeys";

export interface FeaturedCase {
  canonicalUrl: string;
  item: GalleryCase;
}

export function selectFeaturedCase(
  gallery: GalleryIndex,
  journeys: LearningJourneyIndex,
): FeaturedCase | null {
  if (gallery.dataset_version !== journeys.dataset_version) {
    throw new Error("Gallery and learning journey dataset versions do not match.");
  }

  const caseById = new Map(gallery.cases.map((item) => [item.case_id, item]));
  const assessmentById = new Map(
    journeys.assessments.map((assessment) => [assessment.journey_id, assessment]),
  );
  const candidates = journeys.journeys.flatMap((journey) => {
    const item = caseById.get(journey.case_id);
    const assessment = assessmentById.get(journey.journey_id);
    if (
      journey.status === "draft"
      || !item
      || item.status !== "published"
      || item.candidate_methods.length === 0
      || item.excluded_methods.length === 0
      || !journey.scenarios.some((scenario) => scenario.role === "primary")
      || journey.comparisons.length === 0
      || !assessment
    ) {
      return [];
    }
    return [{
      canonicalUrl: journey.canonical_url,
      item,
      journeyId: journey.journey_id,
      missingDimensionCount: assessment.missing_dimensions.length,
      statusRank: journey.status === "complete" ? 0 : 1,
    }];
  });

  candidates.sort((left, right) => (
    left.statusRank - right.statusRank
    || left.missingDimensionCount - right.missingDimensionCount
    || stableIdCompare(left.journeyId, right.journeyId)
  ));
  const selected = candidates[0];
  return selected ? { canonicalUrl: selected.canonicalUrl, item: selected.item } : null;
}

function stableIdCompare(left: string, right: string): number {
  if (left === right) return 0;
  return left < right ? -1 : 1;
}
