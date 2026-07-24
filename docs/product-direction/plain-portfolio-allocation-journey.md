# Plain portfolio allocation: independent journey contract

- Status: implementation brief
- Date: 2026-07-24
- Scope: `portfolio-allocation` only
- Related canonical Case: `portfolio-allocation` (`PA018`)

## Why a separate journey is needed

The existing `portfolio-cvar-allocation` journey uses fixed return scenarios and a CVaR objective.
It teaches tail-risk treatment, training/held-out separation, and sample dependence. It is not a
visualization of the nominal mean-variance QP in `portfolio-allocation`.

Reusing that trace would hide the difference between two decision contracts:

| Case | Inputs | Objective | What must not be inferred |
|---|---|---|---|
| Plain allocation | expected return and covariance | `gamma w^T Sigma w - mu^T w` | tail-risk or out-of-sample guarantee |
| CVaR allocation | finite return scenarios | mean loss plus CVaR | population or future-return guarantee |

## Target lesson

The journey should make the trade-off from one declared risk-aversion value to another visible while
keeping the asset universe, expected returns, covariance matrix, simplex, and concentration cap fixed.
It should expose expected return, variance, maximum asset weight, and feasibility separately.

The contrast is a parameter sensitivity lesson, not a performance ranking or a claim about future
returns. A lower in-model variance is not evidence of lower realized loss.

## Canonical implementation boundary

This requires a new executable problem definition and instance rather than a link to
`PROBLEM_PORTFOLIO_UNCERTAINTY`:

```text
PROBLEM_PORTFOLIO_MEAN_VARIANCE
  └─ INSTANCE_PORTFOLIO_MEAN_VARIANCE_FIXED_4
       ├─ two deterministic gamma-ledger traces
       └─ one non-ranking parameter-sensitivity comparison
```

The implementation must use a fixed, positive-semidefinite covariance matrix and verify simplex and
upper-bound feasibility. The known reference, if shown, is scoped to the declared fixed coefficients;
it is not optimizer-visible future information.

## Required observables

- expected return
- variance
- scalar mean-variance objective
- maximum allocation weight
- simplex residual and bound violation

## Deliberate non-goals

- no CVaR, chance constraint, robust, or distributionally robust claim;
- no trading cost, turnover, taxes, liquidity, or integer lot sizes;
- no empirical backtest or solver wall-clock ranking;
- no inference from this four-asset lesson to a production portfolio.

## Validation and release impact

This is a new problem instance and generated scenario family. Implement it as a Tier C / intentional
dataset-release slice: focused evaluator and scenario tests, deterministic stage, generated artifact
inspection, frontend contracts/build, and browser coverage before any future publish batch.
