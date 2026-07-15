import { parseLearningGraphIndex } from "../../contracts/learning-graph";
import { siteBaseUrl } from "../../data/base-url";

let learningGraphPromise: ReturnType<typeof fetchLearningGraph> | undefined;

export function loadLearningGraph(_signal?: AbortSignal) {
  learningGraphPromise ??= fetchLearningGraph();
  return learningGraphPromise;
}

async function fetchLearningGraph() {
  const response = await fetch(`${siteBaseUrl()}data/learning-graph.json`);
  if (!response.ok) throw new Error(`Learning graph request failed (${response.status}).`);
  return parseLearningGraphIndex(await response.json());
}
