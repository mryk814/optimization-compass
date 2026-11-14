/** Scalar teaching problem: f(x) = (x - 3)^2 / 2, g(x) = lambda |x|. */
export interface ProximalStep {
  x: number;
  gradient: number;
  z: number;
  threshold: number;
  next: number;
  mapping: number;
}

export const PROXIMAL_BUDGET = 12;

export function softThreshold(z: number, threshold: number): number {
  if (Math.abs(z) <= threshold) return 0;
  return Math.sign(z) * (Math.abs(z) - threshold);
}

export function proximalObjective(x: number, lambda: number): number {
  return 0.5 * (x - 3) ** 2 + lambda * Math.abs(x);
}

export function proximalMinimum(lambda: number): number {
  return Math.max(3 - lambda, 0);
}

export function proximalStep(x: number, eta: number, lambda: number): ProximalStep {
  const gradient = x - 3;
  const z = x - eta * gradient;
  const threshold = eta * lambda;
  const next = softThreshold(z, threshold);
  return { x, gradient, z, threshold, next, mapping: (x - next) / eta };
}

export function proximalRun(x0: number, eta: number, lambda: number): ProximalStep[] {
  const steps: ProximalStep[] = [];
  let x = x0;
  for (let k = 0; k < PROXIMAL_BUDGET; k += 1) {
    const step = proximalStep(x, eta, lambda);
    steps.push(step);
    x = step.next;
  }
  return steps;
}
