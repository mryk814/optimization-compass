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
export type Choice = readonly (0 | 1)[];
export function totals(choice: Choice, scenario: Scenario = INTRO) {
  return choice.reduce((sum, take, i) => ({
    weight: sum.weight + take * scenario.items[i].weight,
    value: sum.value + take * scenario.items[i].value,
  }), { weight: 0, value: 0 });
}
/** Fractional knapsack is an exact relaxation here: all weights/values are positive. */
export function relaxation(choice: Choice, scenario: Scenario = INTRO) {
  const fixed = totals(choice, scenario);
  let room = scenario.capacity - fixed.weight;
  if (room < 0) return { feasible: false, bound: -Infinity, fill: [] as number[] };
  let bound = fixed.value;
  const fill: number[] = scenario.items.map((_, i) => choice[i] ?? 0);
  const remaining = scenario.items.map((item, i) => ({ ...item, i })).slice(choice.length).sort((a, b) => b.value / b.weight - a.value / a.weight);
  for (const item of remaining) {
    const part = Math.min(1, room / item.weight);
    fill[item.i] = part;
    bound += part * item.value;
    room -= part * item.weight;
  }
  return { feasible: true, bound, fill };
}
export const nodeId = (choice: Choice) => choice.join("") || "root";
export const branchLabel = (choice: Choice, scenario: Scenario = INTRO) => choice.length
  ? choice.map((take, i) => `${scenario.items[i].name}${take ? "を入れる" : "を外す"}`).join(" → ")
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
  return { scenario, frontier: [[]], best: [...choice], closed: [], message: "まず根を開き、Aを入れる場合と外す場合に分けてみましょう。" };
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
  return { ...state, frontier: [...frontier, [...choice, 1], [...choice, 0]],
    closed: [...state.closed, { choice, reason: "split" }],
    message: `${branchLabel(choice, state.scenario)}を、${state.scenario.items[choice.length].name}を入れる枝と外す枝に分けました。どちらの上界も親の上界を超えません。` };
}
