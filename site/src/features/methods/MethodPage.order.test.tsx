import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, test, vi } from "vitest";

import rawContent from "../../../public/data/content.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import type { EntityLinkIndex } from "../../contracts/entity-links";
import { EntityLinkProvider } from "../../state/entity-links";
import { MethodPage } from "./MethodPage";

const view = {
  dataset_version: rawSiteData.dataset_version,
  generated_at: "2026-07-16T00:00:00Z",
  view_id: "problem-structure",
  preset_id: "VIEW_PROBLEM_STRUCTURE",
  version: "1.0.0",
  title: "Map",
  description: "Map",
  limitations: "No ranking",
  axis: "problem_structure",
  relation_types: ["hierarchy"],
  max_depth: 3,
  filter_policy: {
    mode: "authored_groups",
    groups: [{
      group_id: "root",
      label: "Root",
      label_en: "Root",
      question_ids: [],
      feature_ids: [],
      method_ids: [],
      alternative_ids: [],
    }],
  },
  focus_fallback_entity_types: ["method"],
  root_node_ids: [],
  edges: [],
  entities: [],
  nodes: [],
};

const links: EntityLinkIndex = {
  contract_version: "1.0.0",
  dataset_version: rawSiteData.dataset_version,
  generated_at: "2026-07-16T00:00:00Z",
  entities: [
    {
      entity_type: "method",
      entity_id: "M_BFGS",
      label: "BFGS法",
      summary: "準Newton法",
      canonical_url: "/methods/M_BFGS",
      aliases: [],
      external_url: null,
      relations: [{ relation_type: "learning", target_type: "content", target_id: "bfgs" }],
    },
    {
      entity_type: "content",
      entity_id: "bfgs",
      label: "BFGS",
      summary: "BFGSの教材",
      canonical_url: "/learn/bfgs",
      aliases: [],
      external_url: null,
      relations: [],
    },
  ],
};

describe("MethodPage reading order", () => {
  test("places authored guidance before collapsed machine-oriented detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(async (input: string) => ({
      ok: true,
      json: async () => input.includes("recommendation/site-data.json")
        ? rawSiteData
        : input.includes("failure-modes.json")
          ? {
              contract_version: "1.0.0",
              dataset_version: rawSiteData.dataset_version,
              failure_modes: [],
            }
          : input.includes("content.json")
            ? rawContent
            : view,
    })));

    render(
      <MemoryRouter initialEntries={["/methods/M_BFGS"]}>
        <EntityLinkProvider initialIndex={links}>
          <Routes>
            <Route path="/methods/:methodId" element={<MethodPage />} />
          </Routes>
        </EntityLinkProvider>
      </MemoryRouter>,
    );

    const authoredContent = await screen.findByRole("region", { name: "教材" });
    const disclosureLabel = await screen.findByText("構造化データとトラブルシューティング");
    const technicalDetails = disclosureLabel.closest("details");

    expect(technicalDetails).not.toBeNull();
    expect(
      Boolean(authoredContent.compareDocumentPosition(technicalDetails!) & Node.DOCUMENT_POSITION_FOLLOWING),
    ).toBe(true);
    expect(
      screen.getByRole("heading", { name: "構造化された適用前提", hidden: true }),
    ).not.toBeVisible();
  });
});
