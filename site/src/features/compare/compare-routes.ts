import type { ComparisonMember } from "../../contracts/comparisons";

export const COMPARE_LAB_ROUTE = "/compare";

export function comparisonRoute(comparisonId: string): string {
  return `${COMPARE_LAB_ROUTE}/${comparisonId}`;
}

export function firstMemberPerScenario(members: ComparisonMember[]): ComparisonMember[] {
  const firstByScenario = new Map<string, ComparisonMember>();
  for (const member of members) {
    if (!firstByScenario.has(member.scenario_id)) {
      firstByScenario.set(member.scenario_id, member);
    }
  }
  return [...firstByScenario.values()];
}
