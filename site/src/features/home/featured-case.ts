import type { GalleryCase, GalleryIndex } from "../../contracts/gallery";
import type { LearningJourney, LearningJourneyIndex } from "../../contracts/learning-journeys";
import type { ProblemCatalog, ProblemDefinition, ProblemInstance } from "../../contracts/problems";
import {
  buildReadableProblemFormulation,
  type ReadableProblemFormulation,
} from "./ProblemFormulation";

export interface FeaturedCase {
  canonicalUrl: string;
  item: GalleryCase;
  journey: LearningJourney;
  formulation: ReadableProblemFormulation;
  problemDefinition: ProblemDefinition;
  problemInstance: ProblemInstance;
}

export function selectFeaturedCase(
  gallery: GalleryIndex,
  journeys: LearningJourneyIndex,
  problems: ProblemCatalog,
): FeaturedCase | null {
  const versions = new Set([
    gallery.dataset_version,
    journeys.dataset_version,
    problems.dataset_version,
  ]);
  if (versions.size !== 1) {
    throw new Error("Gallery, learning journey, and problem dataset versions do not match.");
  }

  const caseById = new Map(gallery.cases.map((item) => [item.case_id, item]));
  const assessmentById = new Map(
    journeys.assessments.map((assessment) => [assessment.journey_id, assessment]),
  );
  const instanceById = new Map(
    problems.instances.map((instance) => [instance.problem_instance_id, instance]),
  );
  const definitionById = new Map(
    problems.definitions.map((definition) => [definition.problem_definition_id, definition]),
  );
  const candidates = journeys.journeys.flatMap((journey) => {
    const item = caseById.get(journey.case_id);
    const assessment = assessmentById.get(journey.journey_id);
    const primaryScenario = journey.scenarios.find((scenario) => scenario.role === "primary");
    const problemInstance = primaryScenario
      ? instanceById.get(primaryScenario.problem_instance_id)
      : undefined;
    const problemDefinition = problemInstance
      ? definitionById.get(problemInstance.problem_definition_id)
      : undefined;
    const formulation = problemDefinition && problemInstance
      ? buildReadableProblemFormulation(problemDefinition, problemInstance)
      : null;
    if (
      journey.status === "draft"
      || !item
      || item.status !== "published"
      || item.candidate_methods.length === 0
      || item.excluded_methods.length === 0
      || !primaryScenario
      || journey.comparisons.length === 0
      || !assessment
      || !problemInstance
      || !problemDefinition
      || primaryScenario.problem_definition_id !== problemDefinition.problem_definition_id
      || primaryScenario.problem_instance_id !== problemInstance.problem_instance_id
      || problemInstance.problem_definition_id !== problemDefinition.problem_definition_id
      || !formulation
    ) {
      return [];
    }
    return [{
      canonicalUrl: journey.canonical_url,
      formulation,
      item,
      journey,
      journeyId: journey.journey_id,
      missingDimensionCount: assessment.missing_dimensions.length,
      problemDefinition,
      problemInstance,
      statusRank: journey.status === "complete" ? 0 : 1,
    }];
  });

  candidates.sort((left, right) => (
    left.statusRank - right.statusRank
    || left.missingDimensionCount - right.missingDimensionCount
    || stableIdCompare(left.journeyId, right.journeyId)
  ));
  const selected = candidates[0];
  return selected ? {
    canonicalUrl: selected.canonicalUrl,
    formulation: selected.formulation,
    item: selected.item,
    journey: selected.journey,
    problemDefinition: selected.problemDefinition,
    problemInstance: selected.problemInstance,
  } : null;
}

function stableIdCompare(left: string, right: string): number {
  if (left === right) return 0;
  return left < right ? -1 : 1;
}
