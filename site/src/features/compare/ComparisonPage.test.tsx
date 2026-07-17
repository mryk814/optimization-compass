import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import completeArtifact from "../../../public/data/search-trees/binary-knapsack-bnb-complete.json";
import budgetArtifact from "../../../public/data/search-trees/binary-knapsack-bnb-budget.json";
import searchTreeIndex from "../../../public/data/search-trees/index.json";
import manifest from "../../../public/data/manifest.json";
import scenarios from "../../../public/data/visualization-scenarios.json";
import type { ComparisonIndex } from "../../contracts/comparisons";
import { ComparisonPage } from "./ComparisonPage";

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
    budget: { metric: "oracle_evaluations", value: 4 },
    stopping_policy: "compare at four oracle evaluations",
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
        budget: { metric: "oracle_evaluations", value: 4 },
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
        budget: { metric: "oracle_evaluations", value: 4 },
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

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

type RenderOverrides = {
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
    scenario_id: string;
    runs: Array<{
      implementation_id: string | null;
      implementation_mapping_status: string;
    }>;
  }>;
};

function mutableCompleteArtifact(): MutableTraceContract {
  return structuredClone(completeArtifact) as unknown as MutableTraceContract;
}

function renderPage({
  comparison = comparisonIndex,
  complete = completeArtifact,
  index = searchTreeIndex,
  scenarioIndex = scenarios,
}: RenderOverrides = {}) {
  vi.stubGlobal("fetch", vi.fn(async (input: string | URL | Request) => {
    const url = String(input);
    const body = url.endsWith("data/manifest.json") ? manifest
      : url.endsWith("data/comparisons.json") ? comparison
        : url.endsWith("visualization-scenarios.json") ? scenarioIndex
          : url.endsWith("search-trees/index.json") ? index
            : url.endsWith("binary-knapsack-bnb-complete.json") ? complete
              : url.endsWith("binary-knapsack-bnb-budget.json") ? budgetArtifact
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
    const mismatchedScenarios = structuredClone(scenarios) as unknown as MutableScenarioIndex;
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
