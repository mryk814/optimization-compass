import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import completeArtifact from "../../../public/data/search-trees/binary-knapsack-bnb-complete.json";
import budgetArtifact from "../../../public/data/search-trees/binary-knapsack-bnb-budget.json";
import searchTreeIndex from "../../../public/data/search-trees/index.json";
import manifest from "../../../public/data/manifest.json";
import paretoArtifact from "../../../public/data/visualizations/biobjective-quadratic-pareto-front.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import type { ComparisonIndex } from "../../contracts/comparisons";
import type { VisualizationScenarioIndex } from "../../contracts/visualization-scenarios";
import { ComparisonPage } from "./ComparisonPage";

const alignedEvaluationBudget = 9;
const alignedCompleteArtifact = structuredClone(completeArtifact);
alignedCompleteArtifact.trace.evaluation_budget = alignedEvaluationBudget;
const alignedBudgetArtifact = structuredClone(budgetArtifact);
alignedBudgetArtifact.trace.evaluation_budget = alignedEvaluationBudget;
const alignedScenarios = structuredClone(scenarios);
for (const scenario of alignedScenarios.scenarios.filter(
  (candidate) => candidate.scenario_id.startsWith("SCENARIO_BINARY_KNAPSACK_BNB_"),
)) {
  scenario.experiment.budget.value = alignedEvaluationBudget;
}

const comparisonIndex: ComparisonIndex = {
  contract_version: "2.0.0",
  dataset_version: manifest.dataset_version,
  comparisons: [{
    comparison_id: "COMPARE_KNAPSACK_BNB_BUDGET_TEST",
    canonical_url: "/compare/COMPARE_KNAPSACK_BNB_BUDGET_TEST",
    identity_status: "canonical",
    canonical_comparison_id: "COMPARE_KNAPSACK_BNB_BUDGET_TEST",
    aliases: [],
    mode: "failure_contrast",
    journey_id: "budget-allocation",
    case_id: "budget-allocation",
    problem_definition_id: "PROBLEM_BINARY_KNAPSACK",
    problem_instance_id: "INSTANCE_BINARY_KNAPSACK_4",
    benchmark_context_id: "BENCH_BINARY_KNAPSACK_EDUCATIONAL",
    title_ja: "探索を続けるrunとnode予算停止",
    title_en: "Complete search and a node-budget stop",
    comparison_question: "同じ評価回数で、停止判定はどのように違うか。",
    formulation_summary: "同じ0-1 knapsackと探索順序を使う。",
    fixed_factors: ["problem instance", "branch order", "initial incumbent"],
    changed_factors: ["node budget stopping"],
    seed_policy: "fixed seed 0",
    budget: { metric: "oracle_evaluations", value: alignedEvaluationBudget },
    stopping_policy: "compare at nine oracle evaluations",
    tuning_policy: "fixed depth-first include-first",
    synchronization_axis: "oracle_evaluations",
    metrics: [
      { metric_id: "absolute_gap", label_ja: "絶対gap", direction: "minimize", unit: "objective" },
      { metric_id: "open_nodes", label_ja: "未探索node", direction: "minimize", unit: "nodes" },
    ],
    comparability: "contrast_only",
    ranking_eligible: false,
    fairness_note: "同じ評価回数以下の最後のeventを同期する。",
    caveat: "小さな教育用探索木の停止状態だけを対比する。",
    takeaway: "incumbentがあってもgapとopen nodeが残れば最適性は未証明です。",
    limitations: ["一般のMIP solver性能を比較するものではありません。"],
    source_ids: ["S021", "S022", "S079"],
    last_verified: "2026-07-17",
    members: [
      {
        member_id: "complete-run",
        role: "reference",
        method_id: "M_BRANCH_BOUND",
        scenario_id: "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
        label_ja: "探索継続run",
        label_en: "Continuing run",
        parameters: { node_stop_limit: completeArtifact.trace.stopping.max_nodes },
        budget: { metric: "oracle_evaluations", value: alignedEvaluationBudget },
        artifact: {
          artifact_id: "binary-knapsack-bnb-complete",
          artifact_kind: "executable_trace",
          renderer_family: "search_tree",
          renderer_contract_version: "1.0.0",
          payload_path: "search-trees/binary-knapsack-bnb-complete.json",
        },
      },
      {
        member_id: "budget-run",
        role: "failure_contrast",
        method_id: "M_BRANCH_BOUND",
        scenario_id: "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
        label_ja: "node予算停止run",
        label_en: "Node-budget run",
        parameters: { node_stop_limit: budgetArtifact.trace.stopping.max_nodes },
        budget: { metric: "oracle_evaluations", value: alignedEvaluationBudget },
        artifact: {
          artifact_id: "binary-knapsack-bnb-budget",
          artifact_kind: "executable_trace",
          renderer_family: "search_tree",
          renderer_contract_version: "1.0.0",
          payload_path: "search-trees/binary-knapsack-bnb-budget.json",
        },
      },
    ],
  }],
};

const paretoComparisonIndex: ComparisonIndex = {
  contract_version: "2.0.0",
  dataset_version: manifest.dataset_version,
  comparisons: [{
    comparison_id: "COMPARE_PARETO_PREFERENCE_TEST",
    canonical_url: "/compare/COMPARE_PARETO_PREFERENCE_TEST",
    identity_status: "canonical",
    canonical_comparison_id: "COMPARE_PARETO_PREFERENCE_TEST",
    aliases: [],
    mode: "result_tradeoff",
    journey_id: "EC017",
    case_id: "EC017",
    problem_definition_id: "PROBLEM_BIOBJECTIVE_CONTINUOUS",
    problem_instance_id: "INSTANCE_BIOBJECTIVE_QUADRATIC_2D",
    benchmark_context_id: "BENCH_NLP",
    title_ja: "Pareto preferenceの選択結果",
    title_en: "Pareto preference selections",
    comparison_question: "同じfrontでweightだけを変えると選択点はどう動くか。",
    formulation_summary: "同じ二目的二次問題を使う。",
    fixed_factors: ["sampled points", "analytic front"],
    changed_factors: ["weight_f1"],
    seed_policy: "not applicable",
    budget: { metric: "oracle_evaluations", value: 81 },
    stopping_policy: "81 points complete",
    tuning_policy: "fixed weights",
    synchronization_axis: "oracle_evaluations",
    metrics: [
      { metric_id: "objective_f1", label_ja: "目的 f1", direction: "minimize", unit: "value" },
      { metric_id: "objective_f2", label_ja: "目的 f2", direction: "minimize", unit: "value" },
    ],
    comparability: "not_comparable",
    ranking_eligible: false,
    fairness_note: "同じartifactを使う。",
    caveat: "solver rankingではない。",
    takeaway: "単一bestではない。",
    limitations: ["凸教材に限る。"],
    source_ids: ["S039", "S055", "S068"],
    last_verified: "2026-07-17",
    members: [
      paretoMember("f2-priority", "f₂優先weight", 0.2),
      paretoMember("balanced", "均衡weight", 0.5),
      paretoMember("f1-priority", "f₁優先weight", 0.8),
    ],
  }],
};

function paretoMember(memberId: string, label: string, weight: number) {
  return {
    member_id: memberId,
    role: weight === 0.5 ? "balanced_preference" : "preference_variant",
    method_id: "M_WEIGHTED_SUM",
    scenario_id: "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY",
    label_ja: label,
    label_en: memberId,
    parameters: { weight_f1: weight },
    budget: { metric: "oracle_evaluations", value: 81 },
    artifact: {
      artifact_id: "biobjective-quadratic-pareto-front",
      artifact_kind: "result_visualization" as const,
      renderer_family: "pareto_front" as const,
      renderer_contract_version: "1.1.0",
      payload_path: "visualizations/biobjective-quadratic-pareto-front.json",
    },
  };
}

function paretoScenarioIndex(): VisualizationScenarioIndex {
  const index = structuredClone(scenarios) as unknown as VisualizationScenarioIndex;
  const alternate = index.scenarios.find(
    (candidate) => candidate.scenario_id === "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY",
  );
  const primary = index.scenarios.find(
    (candidate) => candidate.scenario_id === "SCENARIO_BIOBJECTIVE_QUADRATIC",
  );
  if (!alternate || !primary) throw new Error("Pareto scenario fixture is missing");
  alternate.runs = structuredClone(primary.runs);
  return index;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

type RenderOverrides = {
  budget?: unknown;
  comparison?: unknown;
  complete?: unknown;
  index?: unknown;
  scenarioIndex?: unknown;
};

type MutableTraceContract = {
  trace: {
    evaluation_budget: number;
    frames: Array<{ oracle_evaluations: number; payload: {
      absolute_gap: number | null;
      best_feasible_value: number | null;
      incumbent: unknown | null;
      relative_gap: number | null;
    } }>;
    implementation_id: string | null;
    implementation_mapping_status: string;
    profile_id: string;
    stopping: Record<string, unknown>;
  };
};

type MutableScenarioIndex = {
  scenarios: Array<{
    experiment: { budget: { value: number } };
    scenario_id: string;
    runs: Array<{
      implementation_id: string | null;
      implementation_mapping_status: string;
    }>;
  }>;
};

function mutableCompleteArtifact(): MutableTraceContract {
  return structuredClone(alignedCompleteArtifact) as unknown as MutableTraceContract;
}

function mutableBudgetArtifact(): MutableTraceContract {
  return structuredClone(alignedBudgetArtifact) as unknown as MutableTraceContract;
}

function renderPage({
  budget = alignedBudgetArtifact,
  comparison = comparisonIndex,
  complete = alignedCompleteArtifact,
  index = searchTreeIndex,
  scenarioIndex = alignedScenarios,
}: RenderOverrides = {}) {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("data/manifest.json") ? manifest
      : url.endsWith("data/comparisons.json") ? comparison
        : url.endsWith("visualization-scenarios.json") ? scenarioIndex
          : url.endsWith("search-trees/index.json") ? index
            : url.endsWith("binary-knapsack-bnb-complete.json") ? complete
              : url.endsWith("binary-knapsack-bnb-budget.json") ? budget
                : undefined;
    return body
      ? { ok: true, json: async () => structuredClone(body) }
      : { ok: false, status: 404 };
  }));
  return render(
    <MemoryRouter initialEntries={["/compare/COMPARE_KNAPSACK_BNB_BUDGET_TEST"]}>
      <Routes>
        <Route path="/compare/:comparisonId" element={<ComparisonPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

function renderParetoPage({
  artifact = paretoArtifact,
  comparison = paretoComparisonIndex,
  scenarioIndex = paretoScenarioIndex(),
}: { artifact?: unknown; comparison?: unknown; scenarioIndex?: unknown } = {}) {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("data/manifest.json") ? manifest
      : url.endsWith("data/comparisons.json") ? comparison
        : url.endsWith("visualization-scenarios.json") ? scenarioIndex
          : url.endsWith("biobjective-quadratic-pareto-front.json") ? artifact
            : undefined;
    return body
      ? { ok: true, json: async () => structuredClone(body) }
      : { ok: false, status: 404 };
  }));
  return render(
    <MemoryRouter initialEntries={["/compare/COMPARE_PARETO_PREFERENCE_TEST"]}>
      <Routes>
        <Route path="/compare/:comparisonId" element={<ComparisonPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ComparisonPage search-tree renderer", () => {
  test("aligns both members to the latest event at one evaluation and renders unique trees", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { level: 1, name: "探索を続けるrunとnode予算停止" })).toBeVisible();
    fireEvent.change(screen.getByLabelText("評価回数位置"), { target: { value: "4" } });

    await waitFor(() => {
      expect(within(screen.getByLabelText("探索継続runの同期指標")).getByText("探索中")).toBeVisible();
      expect(within(screen.getByLabelText("node予算停止runの同期指標")).getByText("予算停止・未証明")).toBeVisible();
    });
    const completeMetrics = within(screen.getByLabelText("探索継続runの同期指標"));
    expect(completeMetrics.getByText("13")).toBeVisible();
    expect(completeMetrics.getByText("実行可能解あり（feasible）")).toBeVisible();
    expect(completeMetrics.getByText("15.00")).toBeVisible();
    expect(completeMetrics.getByText("2.00")).toBeVisible();
    expect(completeMetrics.getByText("4")).toBeVisible();
    expect(completeMetrics.getByText("3")).toBeVisible();
    expect(screen.getByText(/実行不可能で枝刈り · evaluation 4/u)).toBeVisible();
    expect(screen.getByText(/node予算に到達 · evaluation 4/u)).toBeVisible();
    expect(screen.getByRole("heading", { level: 2, name: "探索継続runの探索木" })).toHaveAttribute(
      "id",
      "comparison-search-tree-heading-0",
    );
    expect(screen.getByRole("heading", { level: 2, name: "node予算停止runの探索木" })).toHaveAttribute(
      "id",
      "comparison-search-tree-heading-1",
    );
    expect(document.querySelectorAll("#comparison-search-tree-heading-0")).toHaveLength(1);
    expect(document.querySelectorAll("#comparison-search-tree-heading-1")).toHaveLength(1);
  });

  test("rejects a comparison descriptor that differs from the search-tree index", async () => {
    const mismatched = structuredClone(searchTreeIndex);
    mismatched.artifacts[0].path = "search-trees/wrong.json";
    renderPage({ index: mismatched });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree scenario/index contract differs from comparison member complete-run.",
    );
  });

  test("rejects an artifact whose identity differs from the validated index entry", async () => {
    const mismatched = { ...structuredClone(completeArtifact), artifact_id: "wrong-artifact" };
    renderPage({ complete: mismatched });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree artifact identity differs from comparison member complete-run.",
    );
  });

  test("rejects a trace profile that differs from its scenario run", async () => {
    const mismatched = mutableCompleteArtifact();
    mismatched.trace.profile_id = "PROFILE_WRONG";
    renderPage({ complete: mismatched });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree execution contract differs from comparison member complete-run.",
    );
  });

  test("rejects an implementation mapping status that differs from its scenario run", async () => {
    const mismatched = mutableCompleteArtifact();
    mismatched.trace.implementation_mapping_status = "unknown";
    mismatched.trace.implementation_id = null;
    renderPage({ complete: mismatched });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree execution contract differs from comparison member complete-run.",
    );
  });

  test("rejects an implementation ID that differs from its scenario run", async () => {
    const mismatchedArtifact = mutableCompleteArtifact();
    mismatchedArtifact.trace.implementation_mapping_status = "supported";
    mismatchedArtifact.trace.implementation_id = "I_TRACE";
    const mismatchedScenarios = structuredClone(alignedScenarios) as unknown as MutableScenarioIndex;
    const scenario = mismatchedScenarios.scenarios.find(
      (candidate) => candidate.scenario_id === "SCENARIO_BINARY_KNAPSACK_BNB_COMPLETE",
    );
    if (!scenario) throw new Error("search-tree scenario fixture is missing");
    scenario.runs[0].implementation_mapping_status = "supported";
    scenario.runs[0].implementation_id = "I_SCENARIO";
    renderPage({ complete: mismatchedArtifact, scenarioIndex: mismatchedScenarios });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree execution contract differs from comparison member complete-run.",
    );
  });

  test("rejects a trace evaluation budget that differs from its scenario experiment", async () => {
    const mismatched = mutableCompleteArtifact();
    mismatched.trace.evaluation_budget += 1;
    renderPage({ complete: mismatched });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree execution contract differs from comparison member complete-run.",
    );
  });

  test("rejects matching trace and scenario budgets that differ from the comparison member", async () => {
    const mismatchedArtifact = mutableBudgetArtifact();
    mismatchedArtifact.trace.evaluation_budget = 8;
    const mismatchedScenarios = structuredClone(alignedScenarios) as unknown as MutableScenarioIndex;
    const scenario = mismatchedScenarios.scenarios.find(
      (candidate) => candidate.scenario_id === "SCENARIO_BINARY_KNAPSACK_BNB_BUDGET",
    );
    if (!scenario) throw new Error("search-tree budget scenario fixture is missing");
    scenario.experiment.budget.value = 8;
    const mismatchedComparison = structuredClone(comparisonIndex);
    mismatchedComparison.comparisons[0].members[1].budget.value = 9;
    renderPage({
      budget: mismatchedArtifact,
      comparison: mismatchedComparison,
      scenarioIndex: mismatchedScenarios,
    });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree execution contract differs from comparison member budget-run.",
    );
  });

  test("rejects a trace node stop that differs from the comparison member", async () => {
    const mismatched = structuredClone(comparisonIndex);
    mismatched.comparisons[0].members[0].parameters.node_stop_limit =
      Number(completeArtifact.trace.stopping.max_nodes) + 1;
    renderPage({ comparison: mismatched });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Search-tree execution contract differs from comparison member complete-run.",
    );
  });

  test("labels missing incumbents as undetermined rather than infeasible", async () => {
    const withoutIncumbent = mutableCompleteArtifact();
    for (const frame of withoutIncumbent.trace.frames.filter((candidate) => candidate.oracle_evaluations === 0)) {
      frame.payload.incumbent = null;
      frame.payload.best_feasible_value = null;
      frame.payload.absolute_gap = null;
      frame.payload.relative_gap = null;
    }
    renderPage({ complete: withoutIncumbent });

    const metrics = within(await screen.findByLabelText("探索継続runの同期指標"));
    expect(metrics.getByText("実行可能解は未発見（undetermined）")).toBeVisible();
    expect(metrics.queryByText(/infeasible/u)).not.toBeInTheDocument();
  });
});

describe("ComparisonPage Pareto preference contract", () => {
  test("renders the artifact-backed decision and objective values for all three weights", async () => {
    renderParetoPage();

    expect(await screen.findByRole("heading", { level: 1, name: "Pareto preferenceの選択結果" })).toBeVisible();
    const f2 = within(screen.getByLabelText("f₂優先weightの選択結果"));
    expect(f2.getByText("weight_f1=0.2")).toBeVisible();
    expect(f2.getByText("(1.6, 1.6)")).toBeVisible();
    expect(f2.getByText("5.12")).toBeVisible();
    expect(f2.getByText("0.32")).toBeVisible();
    const balanced = within(screen.getByLabelText("均衡weightの選択結果"));
    expect(balanced.getByText("(1, 1)")).toBeVisible();
    expect(balanced.getAllByText("2")).toHaveLength(2);
    const f1 = within(screen.getByLabelText("f₁優先weightの選択結果"));
    expect(f1.getByText("(0.4, 0.4)")).toBeVisible();
    expect(f1.getByText("0.32")).toBeVisible();
    expect(f1.getByText("5.12")).toBeVisible();
  });

  test("fails closed when a member weight has no artifact selection", async () => {
    const comparison = structuredClone(paretoComparisonIndex);
    comparison.comparisons[0].members[0].parameters.weight_f1 = 0.3;
    renderParetoPage({ comparison });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Pareto artifact has no preference selection for member f2-priority.",
    );
  });

  test("fails closed when the sensitivity scenario does not expose the shared front artifact run", async () => {
    const scenarioIndex = paretoScenarioIndex();
    const alternate = scenarioIndex.scenarios.find(
      (candidate) => candidate.scenario_id === "SCENARIO_BIOBJECTIVE_PREFERENCE_SENSITIVITY",
    );
    if (!alternate) throw new Error("Pareto sensitivity fixture is missing");
    alternate.runs[0].artifact_id = "different-artifact";
    renderParetoPage({ scenarioIndex });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Scenario comparison run differs from member f2-priority.",
    );
  });

  test("fails closed when a member names a different artifact ID", async () => {
    const comparison = structuredClone(paretoComparisonIndex);
    comparison.comparisons[0].members[1].artifact.artifact_id = "different-artifact";
    renderParetoPage({ comparison });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Scenario comparison members must share one canonical artifact.",
    );
  });

  test("does not bypass member method matching for a Pareto method comparison", async () => {
    const comparison = structuredClone(paretoComparisonIndex);
    comparison.comparisons[0].mode = "method_contrast";
    renderParetoPage({ comparison });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Scenario comparison run differs from member f2-priority.",
    );
  });

  test("fails closed when the scenario budget metric differs from the comparison", async () => {
    const comparison = structuredClone(paretoComparisonIndex);
    comparison.comparisons[0].budget.metric = "sampled_points";
    for (const member of comparison.comparisons[0].members) {
      member.budget.metric = "sampled_points";
    }
    comparison.comparisons[0].synchronization_axis = "sampled_points";
    renderParetoPage({ comparison });

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Scenario comparison artifact contract differs from the comparison.",
    );
  });
});
