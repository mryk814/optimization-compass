import type { ReactNode } from "react";

import { parseSearchTreeFramePayload, type SearchTreeArtifact } from "../../contracts/search-tree";
import { SearchTreeRenderer } from "./SearchTreeRenderer";

type Renderer = (
  artifact: SearchTreeArtifact,
  frameIndex: number,
  visibleLayers?: readonly string[],
  focusTarget?: string,
) => ReactNode;

const rendererRegistry: Readonly<Record<string, Renderer>> = {
  "search_tree@1.0.0": (artifact, frameIndex, visibleLayers, focusTarget) => (
    <SearchTreeRenderer
      focusTarget={focusTarget}
      payload={parseSearchTreeFramePayload(artifact.trace.frames[frameIndex].payload)}
      visibleLayers={visibleLayers}
    />
  ),
};

export function renderVisualizationArtifact(
  artifact: SearchTreeArtifact,
  frameIndex: number,
  visibleLayers?: readonly string[],
  focusTarget?: string,
): ReactNode {
  const key = `${artifact.renderer_family}@${artifact.renderer_contract_version}`;
  const renderer = rendererRegistry[key];
  if (!renderer) throw new Error(`登録されていないrenderer contractです: ${key}`);
  return renderer(artifact, frameIndex, visibleLayers, focusTarget);
}
