import type { AnswerBinding, ViewNode } from "../../contracts/viewspec";
import type {
  AtlasCompatibilityCatalog,
  AtlasStateV1,
} from "../../state/atlas-state";

function displayOrder(left: ViewNode, right: ViewNode): number {
  return left.display_order - right.display_order || left.node_id.localeCompare(right.node_id);
}

export function applyAnswerBindings(
  state: AtlasStateV1,
  bindings: readonly AnswerBinding[],
  catalog: AtlasCompatibilityCatalog,
): AtlasStateV1 {
  const answers = structuredClone(state.answers);
  for (const binding of bindings) {
    const question = catalog.questions[binding.question_id];
    if (!question || !question.allowedAnswers.includes(binding.answer_value)) continue;
    if (binding.answer_value === "unknown") {
      answers[binding.question_id] = { status: "unknown", values: ["unknown"] };
    } else if (question.answerType === "single_choice") {
      answers[binding.question_id] = { status: "answered", values: [binding.answer_value] };
    } else {
      const current = answers[binding.question_id];
      const values = current?.status === "answered" ? [...current.values] : [];
      if (!values.includes(binding.answer_value)) values.push(binding.answer_value);
      answers[binding.question_id] = { status: "answered", values };
    }
  }
  return { ...state, answers };
}

export function matchingBindingNodeIds(
  nodes: readonly ViewNode[],
  state: AtlasStateV1,
): string[] {
  return [...nodes]
    .sort(displayOrder)
    .filter(
      (node) =>
        node.answer_bindings.length > 0 &&
        node.answer_bindings.every((binding) => {
          const answer = state.answers[binding.question_id];
          if (answer?.status === "unknown") return binding.answer_value === "unknown";
          return answer?.status === "answered" && answer.values.includes(binding.answer_value);
        }),
    )
    .map((node) => node.node_id);
}

export function resolveRelatedNodeId(
  nodes: readonly ViewNode[],
  entityType: string,
  entityId: string,
): string | undefined {
  return [...nodes]
    .sort(displayOrder)
    .find((node) =>
      node.related_entities.some(
        (reference) => reference.entity_type === entityType && reference.entity_id === entityId,
      ),
    )?.node_id;
}

export function ancestorIds(
  nodeId: string | undefined,
  parentByChild: ReadonlyMap<string, string>,
): string[] {
  if (!nodeId) return [];
  const closestFirst: string[] = [];
  const seen = new Set([nodeId]);
  let current = parentByChild.get(nodeId);
  while (current !== undefined && !seen.has(current)) {
    closestFirst.push(current);
    seen.add(current);
    current = parentByChild.get(current);
  }
  return closestFirst.reverse();
}

export function visiblePreorder(
  roots: readonly ViewNode[],
  childrenByParent: ReadonlyMap<string, readonly ViewNode[]>,
  expanded: ReadonlySet<string>,
): ViewNode[] {
  const result: ViewNode[] = [];
  const visited = new Set<string>();
  const visit = (node: ViewNode) => {
    if (visited.has(node.node_id)) return;
    visited.add(node.node_id);
    result.push(node);
    if (!expanded.has(node.node_id)) return;
    for (const child of childrenByParent.get(node.node_id) ?? []) visit(child);
  };
  roots.forEach(visit);
  return result;
}
