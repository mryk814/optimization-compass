import type { LearningSliceArtifact } from "../../contracts/learning-slices";
import { FeasibleRegionRenderer, ParetoFrontRenderer } from "./renderers";

const renderers = {
  feasible_region: (artifact: LearningSliceArtifact) => (
    <FeasibleRegionRenderer artifact={artifact as Extract<LearningSliceArtifact, { renderer_family: "feasible_region" }>} />
  ),
  pareto_front: (artifact: LearningSliceArtifact) => (
    <ParetoFrontRenderer artifact={artifact as Extract<LearningSliceArtifact, { renderer_family: "pareto_front" }>} />
  ),
} satisfies Record<LearningSliceArtifact["renderer_family"], (artifact: LearningSliceArtifact) => React.ReactNode>;

export function LearningSliceRenderer({ artifact }: { artifact: LearningSliceArtifact }) {
  return <>{renderers[artifact.renderer_family](artifact)}</>;
}
