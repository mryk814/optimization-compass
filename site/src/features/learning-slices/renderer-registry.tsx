import type { LearningSliceArtifact } from "../../contracts/learning-slices";
import { buildFieldEvolutionPayload } from "../../contracts/field-evolution";
import { FeasibleRegionRenderer, FieldEvolutionRenderer, ParetoFrontRenderer } from "./renderers";

const renderers = {
  feasible_region: (artifact: LearningSliceArtifact) => (
    <FeasibleRegionRenderer artifact={artifact as Extract<LearningSliceArtifact, { renderer_family: "feasible_region" }>} />
  ),
  pareto_front: (artifact: LearningSliceArtifact) => (
    <ParetoFrontRenderer artifact={artifact as Extract<LearningSliceArtifact, { renderer_family: "pareto_front" }>} />
  ),
  field_evolution: (artifact: LearningSliceArtifact) => (
    <FieldEvolutionRenderer payload={buildFieldEvolutionPayload(artifact as Extract<LearningSliceArtifact, { renderer_family: "field_evolution" }>)} />
  ),
} satisfies Record<LearningSliceArtifact["renderer_family"], (artifact: LearningSliceArtifact) => React.ReactNode>;

export function LearningSliceRenderer({ artifact }: { artifact: LearningSliceArtifact }) {
  return <>{renderers[artifact.renderer_family](artifact)}</>;
}
