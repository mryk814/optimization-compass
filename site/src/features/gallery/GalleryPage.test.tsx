import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";
import { MemoryRouter } from "react-router-dom";

import rawGallery from "../../../public/data/gallery.json";
import { parseGalleryIndex } from "../../contracts/gallery";
import {
  caseState,
  countCasesByDomain,
  domainLabel,
  GalleryNote,
  JourneyStatus,
  journeyCompletionLabel,
  journeyStatusLabel,
  journeyStatusSummary,
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

  test("carries explicit candidate reasons and case limitations into the page model", () => {
    const item = parseGalleryIndex(structuredClone(rawGallery)).cases[0];

    expect(item.candidate_methods[0].reason).not.toHaveLength(0);
    expect(item.limitations[0]).not.toHaveLength(0);
  });

  test("uses reader-facing domain and journey labels", () => {
    expect(domainLabel("engineering")).toBe("設計・工学");
    expect(domainLabel("machine-learning")).toBe("機械学習");
    expect(domainLabel("manufacturing")).toBe("製造");
    expect(domainLabel("energy")).toBe("エネルギー");
    expect(domainLabel("public-policy")).toBe("公共政策");
    expect(domainLabel("custom-domain")).toBe("custom-domain");
    expect(journeyStatusLabel("complete")).toBe("定式化・実行・比較あり");
    expect(journeyStatusLabel("partial")).toBe("定式化あり・一部準備中");
    expect(journeyStatusLabel()).toBe("準備中");
    expect(journeyStatusSummary("partial")).toBe("定式化は読めます。実行・比較は順次整備中です。");
  });

  test("summarizes use-case coverage by domain in descending order", () => {
    expect(countCasesByDomain([
      { domain: "science" },
      { domain: "engineering" },
      { domain: "science" },
    ])).toEqual([
      { domain: "science", count: 2 },
      { domain: "engineering", count: 1 },
    ]);
  });
});
