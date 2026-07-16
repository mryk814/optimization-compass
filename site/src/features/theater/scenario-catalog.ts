import {
  findEntity,
  type EntityLinkIndex,
  type LinkedEntity,
} from "../../contracts/entity-links";
import type {
  RendererFamily,
  VisualizationPurpose,
  VisualizationScenario,
} from "../../contracts/visualization-scenarios";

export type TheaterDomain =
  | "continuous"
  | "constrained"
  | "discrete"
  | "black-box"
  | "multi-objective";
export type TheaterPublicationStatus = "published" | "draft" | "hidden";
export type TheaterDifficulty = "intro" | "intermediate";

export interface TheaterCatalogEntry {
  scenario: VisualizationScenario;
  route: string;
  familyId: string;
  domain: TheaterDomain;
  publicationStatus: TheaterPublicationStatus;
  difficulty: TheaterDifficulty;
  methods: LinkedEntity[];
  journey?: LinkedEntity;
  comparisons: LinkedEntity[];
}

export function buildTheaterCatalog(
  scenarios: VisualizationScenario[],
  links: EntityLinkIndex,
): TheaterCatalogEntry[] {
  const entries = scenarios.map((scenario) => {
    const scenarioEntity = findEntity(links, "scenario", scenario.scenario_id);
    const related = scenarioEntity?.relations.flatMap((relation) => {
      const target = findEntity(links, relation.target_type, relation.target_id);
      return target ? [target] : [];
    }) ?? [];
    return {
      scenario,
      route: scenarioRoute(scenario),
      familyId: scenarioFamilyId(scenario),
      domain: scenarioDomain(scenario),
      publicationStatus: publicationStatus(scenario),
      difficulty: scenarioDifficulty(scenario),
      methods: scenario.runs.flatMap((run) => {
        const method = findEntity(links, "method", run.method_id);
        return method ? [method] : [];
      }),
      journey: related.find((entity) => entity.entity_type === "journey"),
      comparisons: related.filter((entity) => entity.entity_type === "comparison"),
    } satisfies TheaterCatalogEntry;
  });
  validatePublicScenarioReachability(entries);
  return entries;
}

export function scenarioRoute(scenario: VisualizationScenario): string {
  const artifactId = scenario.runs[0]?.artifact_id;
  if (!artifactId) throw new Error(`Scenario ${scenario.scenario_id} has no artifact route.`);
  switch (scenario.artifact.renderer_family) {
    case "simplex_geometry":
    case "continuous_trajectory":
    case "generic_metric_history":
      return `/traces/${artifactId}`;
    case "search_tree":
      return `/theater/search-tree/${artifactId}`;
    case "surrogate_uncertainty":
      return `/theater/bayesian-optimization?scenario=${scenario.scenario_id}`;
    case "feasible_region":
    case "pareto_front":
      return `/theater/learning/${scenario.scenario_id}`;
  }
}

export function validatePublicScenarioReachability(entries: TheaterCatalogEntry[]): void {
  const unreachable = entries.filter((entry) => (
    entry.publicationStatus === "published" && !entry.route.startsWith("/")
  ));
  if (unreachable.length > 0) {
    throw new Error(`Published scenarios are unreachable: ${unreachable.map((entry) => entry.scenario.scenario_id).join(", ")}`);
  }
  const publishedIds = new Set(entries
    .filter((entry) => entry.publicationStatus === "published")
    .map((entry) => entry.scenario.scenario_id));
  const missingRecommendations = entries.flatMap((entry) => (
    entry.scenario.lesson.recommended_next_scenario_ids.filter((id) => !publishedIds.has(id))
  ));
  if (missingRecommendations.length > 0) {
    throw new Error(`Published scenario relations are unreachable: ${missingRecommendations.join(", ")}`);
  }
}

export function scenarioFamilyId(scenario: VisualizationScenario): string {
  if (scenario.canonical_scenario_id) {
    return scenario.canonical_scenario_id;
  }
  return [
    scenario.artifact.renderer_family,
    scenario.problem_definition_id,
    scenario.runs[0]?.method_id ?? "no-method",
  ].join(":");
}

function scenarioDomain(scenario: VisualizationScenario): TheaterDomain {
  const renderer = scenario.artifact.renderer_family;
  if (renderer === "search_tree") return "discrete";
  if (renderer === "surrogate_uncertainty") return "black-box";
  if (renderer === "feasible_region") return "constrained";
  if (renderer === "pareto_front") return "multi-objective";
  return "continuous";
}

function publicationStatus(_scenario: VisualizationScenario): TheaterPublicationStatus {
  return "published";
}

function scenarioDifficulty(scenario: VisualizationScenario): TheaterDifficulty {
  return scenario.lesson.comparison_role === "primary_example" ? "intro" : "intermediate";
}

export const purposeLabels: Record<VisualizationPurpose, string> = {
  mechanism: "mechanism",
  comparison: "comparison run",
  failure_contrast: "failure contrast",
  sensitivity: "sensitivity variant",
  application_result: "result / trade-off",
};

export const rendererLabels: Record<RendererFamily, string> = {
  simplex_geometry: "Simplex geometry",
  continuous_trajectory: "Continuous trajectory",
  generic_metric_history: "Metric history",
  search_tree: "Search tree",
  surrogate_uncertainty: "Surrogate uncertainty",
  feasible_region: "Feasible region",
  pareto_front: "Pareto front",
};
