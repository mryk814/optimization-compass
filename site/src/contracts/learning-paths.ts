// Contract for data/learning-paths.json (ADR 0017): authored, ordered walks through
// formulations and content pages, each step carrying the question it answers.

export interface LearningPathStep {
  step: number;
  target_type: "formulation" | "content";
  target_id: string;
  content_id: string | null;
  title_ja: string;
  route: string;
  question_ja: string;
  has_article: boolean;
}

export interface LearningPath {
  path_id: string;
  title_ja: string;
  summary_ja: string;
  goal_ja: string;
  audience_ja: string;
  route: string;
  steps: LearningPathStep[];
}

export interface LearningPathIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  paths: LearningPath[];
}

export function parseLearningPaths(raw: unknown): LearningPathIndex {
  const data = record(raw, "learning paths");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported learning path contract.");
  const paths = array(data.paths, "paths").map((value, index) => {
    const item = record(value, `paths[${index}]`);
    const steps = array(item.steps, "steps").map((entry, position) => {
      const step = record(entry, `steps[${position}]`);
      const targetType = step.target_type;
      if (targetType !== "formulation" && targetType !== "content") throw new Error("Unsupported step target_type.");
      if (step.step !== position + 1) throw new Error("Learning path steps must be numbered in order.");
      if (typeof step.has_article !== "boolean") throw new Error("has_article must be a boolean.");
      return {
        step: position + 1,
        target_type: targetType,
        target_id: text(step.target_id, "target_id"),
        content_id: step.content_id === null ? null : text(step.content_id, "content_id"),
        title_ja: text(step.title_ja, "step title_ja"),
        route: route(step.route, "step route"),
        question_ja: text(step.question_ja, "question_ja"),
        has_article: step.has_article,
      } satisfies LearningPathStep;
    });
    if (steps.length < 2) throw new Error("A learning path needs at least two steps.");
    return {
      path_id: text(item.path_id, "path_id"),
      title_ja: text(item.title_ja, "title_ja"),
      summary_ja: text(item.summary_ja, "summary_ja"),
      goal_ja: text(item.goal_ja, "goal_ja"),
      audience_ja: text(item.audience_ja, "audience_ja"),
      route: route(item.route, "path route"),
      steps,
    } satisfies LearningPath;
  });
  if (new Set(paths.map((path) => path.path_id)).size !== paths.length) throw new Error("Duplicate path ID.");
  return { contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), paths };
}

export function stepKey(step: Pick<LearningPathStep, "target_type" | "target_id">): string {
  return `${step.target_type}:${step.target_id}`;
}

/** Paths and step positions whose route is the given pathname. */
export function stepsAtRoute(index: LearningPathIndex, pathname: string) {
  return index.paths.flatMap((path) => path.steps
    .filter((step) => step.route === pathname)
    .map((step) => ({ path, step })));
}

function record(value: unknown, owner: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`);
  return value as Record<string, unknown>;
}
function array(value: unknown, owner: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`);
  return value;
}
function text(value: unknown, owner: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${owner} must be a non-empty string.`);
  return value;
}
function route(value: unknown, owner: string): string {
  const result = text(value, owner);
  if (!result.startsWith("/") || result.startsWith("//")) throw new Error(`${owner} must be an in-app route.`);
  return result;
}
