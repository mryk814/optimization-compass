/** The same four items as the existing knapsack Trace, ordered by value/weight. */
export const ITEMS = [
  { name: "A", weight: 4, value: 8 },
  { name: "D", weight: 2, value: 4 },
  { name: "B", weight: 3, value: 5 },
  { name: "C", weight: 5, value: 6 },
] as const;
export const CAPACITY = 8;
export interface Item { readonly name: string; readonly weight: number; readonly value: number; }
export interface Scenario { readonly id: "intro" | "advanced"; readonly title: string; readonly items: readonly Item[]; readonly capacity: number; }
export const INTRO: Scenario = { id: "intro", title: "入門・4品", items: ITEMS, capacity: CAPACITY };
export const ADVANCED: Scenario = { id: "advanced", title: "発展・8品", capacity: 10, items: [
  ...ITEMS.slice(0, 3), { name: "E", weight: 4, value: 6 }, { name: "F", weight: 5, value: 7 },
  ITEMS[3], { name: "G", weight: 3, value: 3 }, { name: "H", weight: 2, value: 1 },
] };
export const SCENARIOS = [INTRO, ADVANCED] as const;
export type Decision = 0 | 1 | null;
/** One decision per item; a position beyond the end counts as undecided, so a short prefix is a valid choice. */
export type Choice = readonly Decision[];
export const decisionAt = (choice: Choice, i: number): Decision => choice[i] ?? null;
export function totals(choice: Choice, scenario: Scenario = INTRO) {
  return scenario.items.reduce((sum, item, i) => (choice[i] === 1
    ? { weight: sum.weight + item.weight, value: sum.value + item.value }
    : sum), { weight: 0, value: 0 });
}
/** The choice with one more item decided. */
export function withDecision(choice: Choice, item: number, take: 0 | 1, scenario: Scenario = INTRO): Choice {
  return scenario.items.map((_, i) => (i === item ? take : decisionAt(choice, i)));
}
/** Fractional knapsack is an exact relaxation here: all weights/values are positive. */
export function relaxation(choice: Choice, scenario: Scenario = INTRO) {
  const fixed = totals(choice, scenario);
  let room = scenario.capacity - fixed.weight;
  if (room < 0) return { feasible: false, bound: -Infinity, fill: [] as number[] };
  let bound = fixed.value;
  const fill: number[] = scenario.items.map((_, i) => decisionAt(choice, i) ?? 0);
  const remaining = scenario.items.map((item, i) => ({ ...item, i })).filter((item) => decisionAt(choice, item.i) === null).sort((a, b) => b.value / b.weight - a.value / a.weight);
  for (const item of remaining) {
    const part = Math.min(1, room / item.weight);
    fill[item.i] = part;
    bound += part * item.value;
    room -= part * item.weight;
  }
  return { feasible: true, bound, fill };
}
/**
 * Index of the undecided item the relaxation packs only partly (0 < part < 1), or -1 when it packs
 * whole items only. At most one item is partly packed, so no tie-break is needed; the fixed item order
 * only decides which of several equally dense items is the one cut.
 */
export function fractionalItem(choice: Choice, scenario: Scenario = INTRO): number {
  const { feasible, fill } = relaxation(choice, scenario);
  if (!feasible) return -1;
  return fill.findIndex((part, i) => decisionAt(choice, i) === null && part > 1e-12 && part < 1 - 1e-12);
}
export interface SplitEffect {
  /** The item an "open" decides next: the fractional item of this node's relaxation. */
  splitItem: number;
  /** The item the node's bound packs only partly. It is the same as the split item. */
  fractional: number;
  parentBound: number;
  children: { take: 0 | 1; feasible: boolean; bound: number; drop: number }[];
  /** The larger child bound: what is left of the parent's bound after the split. */
  remaining: number;
  /** True when deciding the split item takes the fractional part away from the bound. */
  lowersBound: boolean;
}
/** What opening a node does to its bound: the parent's bound against each child's. */
export function splitEffect(choice: Choice, scenario: Scenario = INTRO): SplitEffect {
  const parentBound = relaxation(choice, scenario).bound;
  const item = fractionalItem(choice, scenario);
  const children = item < 0 ? [] : ([1, 0] as const).map((take) => {
    const child = relaxation(withDecision(choice, item, take, scenario), scenario);
    return { take, feasible: child.feasible, bound: child.bound, drop: child.feasible ? parentBound - child.bound : Infinity };
  });
  const remaining = children.length ? Math.max(...children.map((child) => child.bound)) : parentBound;
  return {
    splitItem: item,
    fractional: item,
    parentBound, children, remaining,
    lowersBound: remaining < parentBound - 1e-9,
  };
}
/** Decided items as "index:take", in item order. The decisions fix the node, so this is its identity. */
export const nodeId = (choice: Choice) => choice
  .map((take, i) => (take === null || take === undefined ? "" : `${i}:${take}`))
  .filter(Boolean).join(",") || "root";
/** The nodes from the root down to this one: each step decides the fractional item of the node above. */
export function pathTo(choice: Choice, scenario: Scenario = INTRO): Choice[] {
  const target = scenario.items.map((_, i) => decisionAt(choice, i));
  let node: Choice = scenario.items.map(() => null);
  const path = [node];
  while (nodeId(node) !== nodeId(target)) {
    const item = fractionalItem(node, scenario);
    const take = item < 0 ? null : target[item];
    if (take === null) return [target];
    node = withDecision(node, item, take, scenario);
    path.push(node);
  }
  return path;
}
/** Items in the order they were decided on the way to this node. */
export function decisionOrder(choice: Choice, scenario: Scenario = INTRO): number[] {
  const path = pathTo(choice, scenario);
  if (path.length > 1) {
    return path.slice(1).map((node, step) => node.findIndex((take, i) => take !== decisionAt(path[step], i)));
  }
  return scenario.items.map((_, i) => i).filter((i) => decisionAt(choice, i) !== null);
}
export const branchLabel = (choice: Choice, scenario: Scenario = INTRO) => nodeId(choice) !== "root"
  ? decisionOrder(choice, scenario).map((i) => `${scenario.items[i].name}${choice[i] ? "を入れる" : "を外す"}`).join(" → ")
  : "根：まだ何も固定していない";
export interface SearchState {
  scenario: Scenario;
  frontier: Choice[];
  best: Choice;
  closed: { choice: Choice; reason: "bound" | "infeasible" | "leaf" | "split" }[];
  message: string;
}
export function startSearch(choice: Choice, scenario: Scenario = INTRO): SearchState {
  if (choice.length !== scenario.items.length || totals(choice, scenario).weight > scenario.capacity) throw new Error("A feasible full choice is required");
  return { scenario, frontier: [scenario.items.map(() => null)], best: [...choice], closed: [], message: "まず根を開き、端数になる品を入れる場合と外す場合に分けてみましょう。" };
}
export function certificate(state: SearchState) {
  const lower = totals(state.best, state.scenario).value;
  const upper = Math.max(lower, ...state.frontier.map((choice) => relaxation(choice, state.scenario).bound));
  return { lower, upper, gap: upper - lower, proven: upper <= lower };
}
export function act(state: SearchState, id: string, action: "open" | "prune"): SearchState {
  const choice = state.frontier.find((node) => nodeId(node) === id);
  if (!choice) return state;
  const relaxed = relaxation(choice, state.scenario);
  const lower = totals(state.best, state.scenario).value;
  const removable = !relaxed.feasible || relaxed.bound <= lower;
  if (action === "prune" && !removable) return {
    ...state, message: `この枝の上界は暫定値 ${lower} を超えています。もっと良い組合せがあるかもしれないので、まだ除けません。`,
  };
  if (action === "open" && removable) return {
    ...state, message: relaxed.feasible
      ? `上界が暫定値 ${lower} 以下なので、この先の組合せを試さずに除けます。「調べずに除く」を選んでみましょう。`
      : "固定した品だけで容量を超えています。この枝は実行不能なので除けます。",
  };
  const frontier = state.frontier.filter((node) => nodeId(node) !== id);
  if (action === "prune") return {
    ...state, frontier,
    closed: [...state.closed, { choice, reason: relaxed.feasible ? "bound" : "infeasible" }],
    message: relaxed.feasible
      ? `${branchLabel(choice, state.scenario)}を除きました。上界が ${lower} 以下なら、この枝に実行可能な解があっても暫定解を改善できません。`
      : `${branchLabel(choice, state.scenario)}を除きました。容量を超えた固定品を、残りの品の選び方で軽くすることはできません。`,
  };
  // An integral relaxed optimum is also a feasible full solution: no split is needed.
  if (relaxed.fill.every((part) => part === 0 || part === 1)) {
    const best = relaxed.fill as (0 | 1)[];
    return { ...state, frontier, best, closed: [...state.closed, { choice, reason: "leaf" }],
      message: `${branchLabel(choice, state.scenario)}では分割せずに詰められました。${relaxed.bound} 点の実行可能解に更新し、この枝を閉じます。全体の上界と見比べてみましょう。` };
  }
  const item = fractionalItem(choice, state.scenario);
  return { ...state, frontier: [...frontier, withDecision(choice, item, 1, state.scenario), withDecision(choice, item, 0, state.scenario)],
    closed: [...state.closed, { choice, reason: "split" }],
    message: `${branchLabel(choice, state.scenario)}を、端数だった${state.scenario.items[item].name}を入れる枝と外す枝に分けました。どちらの上界も親の上界を超えません。` };
}
