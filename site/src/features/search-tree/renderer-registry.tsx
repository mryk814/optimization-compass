import type { ReactNode } from "react";

import { parseSearchTreeFramePayload, type SearchTreeArtifact } from "../../contracts/search-tree";
import { SearchTreeRenderer } from "./SearchTreeRenderer";

type Renderer = (artifact: SearchTreeArtifact, frameIndex: number) => ReactNode;

const rendererRegistry: Readonly<Record<string, Renderer>> = {
  "search_tree@1.0.0": (artifact, frameIndex) => (
    <SearchTreeRenderer payload={parseSearchTreeFramePayload(artifact.trace.frames[frameIndex].payload)} />
  ),
};

export function renderVisualizationArtifact(artifact: SearchTreeArtifact, frameIndex: number): ReactNode {
  const key = `${artifact.renderer_family}@${artifact.renderer_contract_version}`;
  const renderer = rendererRegistry[key];
  if (!renderer) throw new Error(`登録されていないrenderer contractです: ${key}`);
  return renderer(artifact, frameIndex);
}
