export const COMPARE_LAB_ROUTE = "/compare";

export function comparisonRoute(comparisonId: string): string {
  return `${COMPARE_LAB_ROUTE}/${comparisonId}`;
}
