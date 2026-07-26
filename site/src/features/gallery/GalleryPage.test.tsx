import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import rawGallery from "../../../public/data/gallery.json";
import { parseGalleryIndex, type GalleryCase } from "../../contracts/gallery";
import type { LearningJourney } from "../../contracts/learning-journeys";
import {
  caseState,
  countCasesByDomain,
  GalleryDomainOverview,
  GalleryNote,
  GalleryTakeaway,
  JourneyProgress,
  JourneyStatus,
  journeyCompletionLabel,
  journeyStatusLabel,
  journeyStatusSummary,
  sameStringSet,
  selectFeaturedCases,
  splitGalleryNote,
} from "./GalleryPage";

describe("gallery Atlas state", () => {
  test("uses the version carried by the gallery release", () => {
    const item = {
      map_node_id: "method:M_BAYESIAN_OPT_GP",
      question_answers: { Q01: "continuous", Q02: "unknown" },
    };

    const state = caseState(item, "0.3.0");

    expect(state.datasetVersion).toBe("0.3.0");
    expect(state.selectedNodeId).toBe("method:M_BAYESIAN_OPT_GP");
    expect(state.answers.Q01).toEqual({ status: "answered", values: ["continuous"] });
    expect(state.answers.Q02).toEqual({ status: "unknown", values: ["unknown"] });
  });
});

describe("gallery learning journey status", () => {
  test("shows formulation, run, and comparison as a compact accessible progression", () => {
    render(<JourneyProgress journey={{
      status: "partial",
      scenarios: [{
        scenario_id: "SCENARIO_EXAMPLE",
        role: "primary",
        canonical_url: "/traces/example",
        problem_definition_id: "PROBLEM_EXAMPLE",
        problem_instance_id: "INSTANCE_EXAMPLE",
      }],
      comparisons: [],
    } as Pick<LearningJourney, "status" | "scenarios" | "comparisons">} />);

    const progress = screen.getByRole("img", {
      name: "定式化あり、実行あり、比較未接続。定式化は読めます。実行・比較は順次整備中です。",
    });
    expect(progress).toHaveTextContent("定式化");
    expect(progress).toHaveTextContent("実行");
    expect(progress).toHaveTextContent("比較");
    expect(progress.querySelectorAll(".is-ready")).toHaveLength(2);
    expect(progress.querySelectorAll(".is-pending")).toHaveLength(1);
  });

  test("keeps coverage counts behind a disclosure while preserving domain filtering", () => {
    const onSelect = vi.fn();
    render(
      <GalleryDomainOverview
        activeDomain="all"
        featuredItems={[
          { domain: "engineering", label_ja: "設計・工学", count: 7 },
          { domain: "control", label_ja: "制御", count: 3 },
        ]}
        largestDomainCount={7}
        onSelect={onSelect}
        remainingItems={[{ domain: "science", label_ja: "科学・推定", count: 2 }]}
      />,
    );

    expect(screen.getByText("3領域の掲載数")).toBeVisible();
    expect(screen.getByRole("button", { name: /設計・工学/u })).not.toBeVisible();

    fireEvent.click(screen.getByText("分野の広がりを見る"));
    fireEvent.click(screen.getByRole("button", { name: /設計・工学/u }));

    expect(onSelect).toHaveBeenCalledWith("engineering");
    expect(screen.getByRole("button", { name: /設計・工学/u })).not.toBeVisible();
  });

  test("translates missing canonical routes into reader-facing labels", () => {
    expect(journeyCompletionLabel("missing_primary_scenario")).toBe("主な実行例未接続");
    expect(journeyCompletionLabel("missing_comparison")).toBe("比較ページ未接続");
    expect(journeyCompletionLabel("missing_static_text_alternative")).toBe("可視化のテキスト説明未整備");
    expect(journeyCompletionLabel("unknown_internal_code")).toBe("接続状況を確認中");
  });

  test("keeps connection diagnostics behind a reader-controlled disclosure", () => {
    render(<JourneyStatus journey={{
      status: "partial",
      completion_reasons: ["missing_primary_scenario", "missing_comparison"],
    }} />);

    expect(screen.getByLabelText(
      "学習の流れの接続状況。定式化は読めます。実行・比較は順次整備中です。",
    )).toBeVisible();
    expect(screen.getByText("主な実行例未接続")).not.toBeVisible();

    fireEvent.click(screen.getByText("接続状況を確認（2）"));

    expect(screen.getByText("主な実行例未接続")).toBeVisible();
  });

  test("renders links and inline formulas without exposing authoring syntax", () => {
    render(
      <MemoryRouter>
        <p>
          <GalleryNote>
            {"[SO(3)の表現](#/learn/concept.so3-rotation-representation)では$q$と$-q$を同一視する。"}
          </GalleryNote>
        </p>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "SO(3)の表現" })).toHaveAttribute(
      "href",
      "/learn/concept.so3-rotation-representation",
    );
    expect(screen.getByText("q", { selector: "code" })).toBeVisible();
    expect(screen.getByText("-q", { selector: "code" })).toBeVisible();
    expect(screen.queryByText(/\[SO\(3\)の表現\]|\$q\$/u)).not.toBeInTheDocument();
  });

  test("keeps the first takeaway sentence visible and defers the dense explanation", () => {
    const { container } = render(
      <MemoryRouter>
        <GalleryTakeaway>
          {"最初に固定条件を確認する。次に$q$と$-q$の同値性を点検する。"}
        </GalleryTakeaway>
      </MemoryRouter>,
    );

    expect(screen.getByText("最初に固定条件を確認する。")).toBeVisible();
    expect(screen.getByText(/次に/u)).not.toBeVisible();

    fireEvent.click(screen.getByText("判断の根拠と実務上の注意を読む"));

    expect(screen.getByText(/次に/u)).toBeVisible();
    expect(within(container).getByText("q", { selector: "code" })).toBeVisible();
  });

  test("splits dense notes without losing text and compares limitation sets without order dependence", () => {
    expect(splitGalleryNote("要点。根拠。")).toEqual({ lead: "要点。", detail: "根拠。" });
    expect(splitGalleryNote("要点だけ")).toEqual({ lead: "要点だけ", detail: "" });
    expect(sameStringSet(["制約A", "制約B"], ["制約B", "制約A"])).toBe(true);
    expect(sameStringSet(["制約A"], ["制約A", "制約B"])).toBe(false);
  });

  test("carries explicit candidate reasons and case limitations into the page model", () => {
    const item = parseGalleryIndex(structuredClone(rawGallery)).cases[0];

    expect(item.candidate_methods[0].reason).not.toHaveLength(0);
    expect(item.limitations[0]).not.toHaveLength(0);
  });

  test("uses generated reader-facing domain and journey labels", () => {
    const index = parseGalleryIndex(structuredClone(rawGallery));
    expect(index.cases.find((item) => item.domain === "engineering")?.domain_label_ja)
      .toBe("設計・工学");
    expect(index.cases.find((item) => item.domain === "transportation")?.domain_label_ja)
      .toBe("交通・モビリティ");
    expect(journeyStatusLabel("complete")).toBe("定式化・実行・比較あり");
    expect(journeyStatusLabel("partial")).toBe("定式化あり・一部準備中");
    expect(journeyStatusLabel()).toBe("準備中");
    expect(journeyStatusSummary("partial")).toBe("定式化は読めます。実行・比較は順次整備中です。");
  });

  test("summarizes use-case coverage by domain in descending order", () => {
    expect(countCasesByDomain([
      { domain: "science", domain_label_ja: "科学・推定" },
      { domain: "engineering", domain_label_ja: "設計・工学" },
      { domain: "science", domain_label_ja: "科学・推定" },
    ])).toEqual([
      { domain: "science", label_ja: "科学・推定", count: 2 },
      { domain: "engineering", label_ja: "設計・工学", count: 1 },
    ]);
  });

  test("features complete journeys across different domains before the full catalog", () => {
    const cases = [
      { case_id: "A", domain: "engineering" },
      { case_id: "B", domain: "engineering" },
      { case_id: "C", domain: "finance" },
      { case_id: "D", domain: "healthcare" },
    ] as GalleryCase[];
    const journeys = [
      { case_id: "A", status: "complete" },
      { case_id: "B", status: "complete" },
      { case_id: "C", status: "complete" },
      { case_id: "D", status: "partial" },
    ] as LearningJourney[];

    expect(selectFeaturedCases(cases, journeys, 3).map((item) => item.case_id))
      .toEqual(["A", "C", "B"]);
  });
});
