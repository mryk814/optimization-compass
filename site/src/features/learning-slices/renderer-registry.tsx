import type { LearningSliceArtifact } from "../../contracts/learning-slices";
import { buildFieldEvolutionPayload } from "../../contracts/field-evolution";
import { FeasibleRegionRenderer, FieldEvolutionRenderer, ParetoFrontRenderer } from "./renderers";

export type InitialRunRole = "primary" | "comparison" | "failure_contrast";
type Renderer = (artifact: LearningSliceArtifact, initialRunRole?: InitialRunRole) => React.ReactNode;

const renderers = {
  feasible_region: (artifact: LearningSliceArtifact) => (
    <FeasibleRegionRenderer artifact={artifact as Extract<LearningSliceArtifact, { renderer_family: "feasible_region" }>} />
  ),
  pareto_front: (artifact: LearningSliceArtifact) => (
    <ParetoFrontRenderer artifact={artifact as Extract<LearningSliceArtifact, { renderer_family: "pareto_front" }>} />
  ),
  field_evolution: (artifact: LearningSliceArtifact, initialRunRole?: InitialRunRole) => (
    <FieldEvolutionRenderer payload={buildFieldEvolutionPayload(artifact as Extract<LearningSliceArtifact, { renderer_family: "field_evolution" }>)} initialRunRole={initialRunRole} />
  ),
} satisfies Record<LearningSliceArtifact["renderer_family"], Renderer>;

export function LearningSliceRenderer({ artifact, initialRunRole }: { artifact: LearningSliceArtifact; initialRunRole?: InitialRunRole }) {
  if (artifact.renderer_family === "field_evolution") {
    return <>{renderers.field_evolution(artifact, initialRunRole)}</>;
  }
  return <>{renderers[artifact.renderer_family](artifact)}</>;
}
