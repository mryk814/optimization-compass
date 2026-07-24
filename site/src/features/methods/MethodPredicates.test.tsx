import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import rawSiteData from "../../../public/data/recommendation/site-data.json";
import { parseSiteData } from "../../contracts/site-data";
import { MethodPredicates } from "./MethodPredicates";

describe("MethodPredicates", () => {
  test("renders the canonical predicate and coverage used by recommendation", () => {
    const data = parseSiteData(rawSiteData);
    render(<MethodPredicates data={data} methodId="M_BFGS" />);

    expect(screen.getByRole("heading", { name: "構造化された適用前提" })).toBeVisible();
    expect(screen.getByText(/推薦・比較・実装用プロンプトで再利用/u)).toBeVisible();
    expect(screen.getAllByText(/not differentiable|微分/u).length).toBeGreaterThan(0);

    expect(screen.getByText("データ収録状況")).toBeVisible();
    expect(screen.getByText("移行済み")).not.toBeVisible();
    fireEvent.click(screen.getByText("データ収録状況"));
    expect(screen.getByText("移行済み")).toBeVisible();
    expect(screen.getByText(/推薦で使う前提・非対応条件を移行済み/u)).toBeVisible();
  });
});
