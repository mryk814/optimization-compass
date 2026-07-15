import { parseLearningGraphIndex } from "../../contracts/learning-graph";
import { siteBaseUrl } from "../../data/base-url";

export async function loadLearningGraph(signal?: AbortSignal) {
  const response = await fetch(`${siteBaseUrl()}data/learning-graph.json`, { signal });
  if (!response.ok) throw new Error(`Learning graph request failed (${response.status}).`);
  return parseLearningGraphIndex(await response.json());
}
