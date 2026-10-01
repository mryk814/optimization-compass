import { parseContentIndex, type AtlasContentIndex } from "../../contracts/atlas-content";
import { parseFormulationAtlas, type FormulationAtlasIndex } from "../../contracts/formulation-atlas";
import { parseLearningPaths, type LearningPathIndex } from "../../contracts/learning-paths";
import { siteBaseUrl } from "../../data/base-url";

let atlasPromise: Promise<FormulationAtlasIndex> | undefined;
let pathPromise: Promise<LearningPathIndex> | undefined;
let contentPromise: Promise<AtlasContentIndex> | undefined;

async function fetchJson(name: string, label: string): Promise<unknown> {
  const response = await fetch(`${siteBaseUrl()}data/${name}`);
  if (!response.ok) throw new Error(`${label}の読み込みに失敗しました (${response.status})。`);
  return response.json();
}

export function loadFormulationAtlas(): Promise<FormulationAtlasIndex> {
  atlasPromise ??= fetchJson("formulation-atlas.json", "定式化の辞書").then(parseFormulationAtlas);
  atlasPromise.catch(() => { atlasPromise = undefined; });
  return atlasPromise;
}

export function loadLearningPaths(): Promise<LearningPathIndex> {
  pathPromise ??= fetchJson("learning-paths.json", "学ぶ道筋").then(parseLearningPaths);
  pathPromise.catch(() => { pathPromise = undefined; });
  return pathPromise;
}

export function loadContentIndex(): Promise<AtlasContentIndex> {
  contentPromise ??= fetchJson("content.json", "教材").then(parseContentIndex);
  contentPromise.catch(() => { contentPromise = undefined; });
  return contentPromise;
}
