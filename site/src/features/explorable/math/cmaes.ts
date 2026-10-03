/**
 * CMA-ES in two dimensions, following Hansen's tutorial (S058) with its default parameters:
 * λ = 6 samples, μ = 3 parents with log weights, cumulative step-size adaptation, and rank-one
 * plus rank-μ covariance updates. A seeded mulberry32 generator and Box–Muller make every run
 * reproducible, so the figure and the article's table show the same numbers.
 */
export type Vec = readonly [number, number];
export type Mat = readonly [readonly [number, number], readonly [number, number]];

export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussPair(random: () => number): Vec {
  const u1 = Math.max(random(), 1e-12);
  const u2 = random();
  const r = Math.sqrt(-2 * Math.log(u1));
  return [r * Math.cos(2 * Math.PI * u2), r * Math.sin(2 * Math.PI * u2)];
}

const S2 = Math.SQRT1_2;

/** A valley along the diagonal x = y: curvature 1 along it and `ratio²` across it. */
export function valley(x: Vec, ratio: number): number {
  const u = (x[0] + x[1]) * S2;
  const v = (x[0] - x[1]) * S2;
  return u * u + ratio * ratio * v * v;
}

export interface Eigen {
  values: Vec;
  /** Unit eigenvectors, largest eigenvalue first. */
  vectors: readonly [Vec, Vec];
}

export function eigen2(c: Mat): Eigen {
  const [a, b, d] = [c[0][0], c[0][1], c[1][1]];
  const mid = (a + d) / 2;
  const half = Math.hypot((a - d) / 2, b);
  const l1 = mid + half;
  const l2 = mid - half;
  let v: Vec = Math.abs(b) > 1e-15 ? [l1 - d, b] : a >= d ? [1, 0] : [0, 1];
  const n = Math.hypot(v[0], v[1]);
  v = [v[0] / n, v[1] / n];
  return { values: [l1, l2], vectors: [v, [-v[1], v[0]]] };
}

/** Square root of the eigenvalue ratio: how many times longer the ellipse is than wide. */
export function axisRatio(c: Mat): number {
  const { values } = eigen2(c);
  return Math.sqrt(values[0] / Math.max(values[1], 1e-300));
}

export interface Sample {
  x: Vec;
  /** Step before scaling by σ: x = m + σ y. */
  y: Vec;
  f: number;
}

export interface Generation {
  index: number;
  mean: Vec;
  sigma: number;
  cov: Mat;
  /** Sorted best first; the first μ are the parents of the next mean. */
  samples: Sample[];
}

export interface CmaParameters {
  lambda: number;
  mu: number;
  weights: number[];
  muEff: number;
  cSigma: number;
  dSigma: number;
  cC: number;
  c1: number;
  cMu: number;
}

export function defaultParameters(adaptShape: boolean): CmaParameters {
  const n = 2;
  const lambda = 4 + Math.floor(3 * Math.log(n));
  const mu = Math.floor(lambda / 2);
  const raw = Array.from({ length: mu }, (_, i) => Math.log((lambda + 1) / 2) - Math.log(i + 1));
  const total = raw.reduce((sum, w) => sum + w, 0);
  const weights = raw.map((w) => w / total);
  const muEff = 1 / weights.reduce((sum, w) => sum + w * w, 0);
  const cSigma = (muEff + 2) / (n + muEff + 5);
  const dSigma = 1 + 2 * Math.max(0, Math.sqrt((muEff - 1) / (n + 1)) - 1) + cSigma;
  const cC = (4 + muEff / n) / (n + 4 + (2 * muEff) / n);
  const c1 = adaptShape ? 2 / ((n + 1.3) ** 2 + muEff) : 0;
  const cMu = adaptShape ? Math.min(1 - c1, (2 * (muEff - 2 + 1 / muEff)) / ((n + 2) ** 2 + muEff)) : 0;
  return { lambda, mu, weights, muEff, cSigma, dSigma, cC, c1, cMu };
}

export interface CmaRun {
  generations: Generation[];
  parameters: CmaParameters;
}

/**
 * Runs `count` generations. With `adaptShape` false the covariance stays the identity and only
 * σ adapts: an isotropic evolution strategy, the comparison in the figure.
 */
export function runCmaes(options: {
  mean: Vec;
  sigma: number;
  ratio: number;
  seed: number;
  adaptShape: boolean;
  count: number;
}): CmaRun {
  const n = 2;
  const p = defaultParameters(options.adaptShape);
  const chi = Math.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n));
  const random = mulberry32(options.seed);
  let mean: Vec = options.mean;
  let sigma = options.sigma;
  let cov: Mat = [[1, 0], [0, 1]];
  let ps: Vec = [0, 0];
  let pc: Vec = [0, 0];
  const generations: Generation[] = [];
  for (let g = 0; g < options.count; g += 1) {
    const { values, vectors: [v1, v2] } = eigen2(cov);
    const d: Vec = [Math.sqrt(Math.max(values[0], 1e-300)), Math.sqrt(Math.max(values[1], 1e-300))];
    const samples: Sample[] = [];
    for (let k = 0; k < p.lambda / 2; k += 1) {
      const z1 = gaussPair(random);
      const z2 = gaussPair(random);
      for (const z of [[z1[0], z2[0]], [z1[1], z2[1]]] as const) {
        const y: Vec = [v1[0] * d[0] * z[0] + v2[0] * d[1] * z[1], v1[1] * d[0] * z[0] + v2[1] * d[1] * z[1]];
        const x: Vec = [mean[0] + sigma * y[0], mean[1] + sigma * y[1]];
        samples.push({ x, y, f: valley(x, options.ratio) });
      }
    }
    // A stable sort keeps ties in sampling order, as Python's sort does.
    samples.sort((left, right) => left.f - right.f);
    generations.push({ index: g, mean, sigma, cov, samples });

    const weighted = (axis: number) => p.weights.reduce((sum, w, i) => sum + w * samples[i].y[axis], 0);
    const yw: Vec = [weighted(0), weighted(1)];
    mean = [mean[0] + sigma * yw[0], mean[1] + sigma * yw[1]];
    const c1y = v1[0] * yw[0] + v1[1] * yw[1];
    const c2y = v2[0] * yw[0] + v2[1] * yw[1];
    const whitened: Vec = [v1[0] * (c1y / d[0]) + v2[0] * (c2y / d[1]), v1[1] * (c1y / d[0]) + v2[1] * (c2y / d[1])];
    const k = Math.sqrt(p.cSigma * (2 - p.cSigma) * p.muEff);
    ps = [(1 - p.cSigma) * ps[0] + k * whitened[0], (1 - p.cSigma) * ps[1] + k * whitened[1]];
    const psNorm = Math.hypot(ps[0], ps[1]);
    const hSigma = psNorm / Math.sqrt(1 - (1 - p.cSigma) ** (2 * (g + 1))) < (1.4 + 2 / (n + 1)) * chi ? 1 : 0;
    const kc = Math.sqrt(p.cC * (2 - p.cC) * p.muEff);
    pc = [(1 - p.cC) * pc[0] + hSigma * kc * yw[0], (1 - p.cC) * pc[1] + hSigma * kc * yw[1]];
    const dh = (1 - hSigma) * p.cC * (2 - p.cC);
    const rank = (a: number, b: number) => p.weights.reduce((sum, w, i) => sum + w * samples[i].y[a] * samples[i].y[b], 0);
    const entry = (a: number, b: number) => (
      (1 - p.c1 - p.cMu) * cov[a][b] + p.c1 * (pc[a] * pc[b] + dh * cov[a][b]) + p.cMu * rank(a, b)
    );
    cov = [[entry(0, 0), entry(0, 1)], [entry(1, 0), entry(1, 1)]];
    sigma *= Math.exp((p.cSigma / p.dSigma) * (psNorm / chi - 1));
  }
  return { generations, parameters: p };
}
