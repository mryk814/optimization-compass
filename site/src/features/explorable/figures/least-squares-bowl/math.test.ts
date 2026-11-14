import { describe, expect, it } from "vitest";

import { evaluateLine, fitLine } from "./math";

const ARTICLE_POINTS = [{ t: 0, y: 1 }, { t: 1, y: 2 }, { t: 2, y: 2 }, { t: 3, y: 4 }];

describe("least-squares math", () => {
  it("solves the article's four points exactly and makes the residuals orthogonal to [1, t]", () => {
    const line = fitLine(ARTICLE_POINTS)!;
    expect(line.a).toBeCloseTo(0.9, 12);
    expect(line.b).toBeCloseTo(0.9, 12);
    const fit = evaluateLine(ARTICLE_POINTS, line);
    expect(fit.sse).toBeCloseTo(0.7, 12);
    expect(fit.residuals.map((r) => Number(r.toFixed(10)))).toEqual([0.1, 0.2, -0.7, 0.4]);
    expect(fit.residualSum).toBeCloseTo(0, 12);
    expect(fit.residualMoment).toBeCloseTo(0, 12);
  });

  it("has no unique line when every t is the same", () => {
    expect(fitLine([{ t: 1, y: 0 }, { t: 1, y: 2 }])).toBeUndefined();
  });
});
