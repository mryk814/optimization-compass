import { describe, expect, test } from "vitest";

import rawEntityLinks from "../../../public/data/entity-links.json";
import rawFailureModes from "../../../public/data/failure-modes.json";
import rawGallery from "../../../public/data/gallery.json";
import rawManifest from "../../../public/data/manifest.json";
import rawSiteData from "../../../public/data/recommendation/site-data.json";
import { parseEntityLinkIndex } from "../../contracts/entity-links";
import { parseFailureModeIndex } from "../../contracts/failure-modes";
import { parseGalleryIndex } from "../../contracts/gallery";
import { parseSiteManifest } from "../../contracts/manifest";
import { parseSiteData } from "../../contracts/site-data";
import { toRecommendationAnswers } from "../../state/atlas-state";
import { caseState } from "../gallery/GalleryPage";
import { recommend } from "../diagnose/recommend";
import {
  createDiagnosePromptDraft,
  createGalleryPromptDraft,
  createImplementationPromptPack,
  renderImplementationPromptMarkdown,
} from "./implementation-prompt";
import type { PromptSupportData } from "./support-data";

function support(): PromptSupportData {
  return {
    manifest: parseSiteManifest(structuredClone(rawManifest)),
    data: parseSiteData(structuredClone(rawSiteData)),
    failureModes: parseFailureModeIndex(structuredClone(rawFailureModes)),
    entityLinks: parseEntityLinkIndex(structuredClone(rawEntityLinks)),
  };
}

function representativeCase() {
  const item = parseGalleryIndex(structuredClone(rawGallery)).cases.find((entry) => entry.case_id === "EC019");
  if (!item) throw new Error("EC019 fixture is missing.");
  return item;
}

describe("ImplementationPromptPack", () => {
  test("renders Diagnose context deterministically with every recommendation band and authority metadata", () => {
    const artifacts = support();
    const item = representativeCase();
    const state = caseState(item, artifacts.data.dataset_version);
    const result = recommend(artifacts.data, toRecommendationAnswers(state), {
      expected_dataset_version: artifacts.data.dataset_version,
    });
    const draft = createDiagnosePromptDraft({
      state,
      result,
      support: artifacts,
      generatedAt: "2026-07-15T05:00:00.000Z",
    });
    const first = createImplementationPromptPack(draft, draft.initial_form);
    const second = createImplementationPromptPack(draft, structuredClone(draft.initial_form));

    expect(first).toEqual(second);
    expect(renderImplementationPromptMarkdown(first)).toBe(renderImplementationPromptMarkdown(second));
    expect(first.contract_version).toBe("1.0.0");
    expect(first.dataset_version).toBe(rawSiteData.dataset_version);
    expect(first.generated_at).toBe("2026-07-15T05:00:00.000Z");
    expect(first.atlas_context.alternatives_first.length).toBeGreaterThan(0);
    expect(first.atlas_context.first_candidates.length).toBeGreaterThan(0);
    expect(first.atlas_context.conditional_candidates.length).toBeGreaterThan(0);
    expect(first.atlas_context.excluded_methods.length).toBeGreaterThan(0);
    expect(first.atlas_context.method_conditions.length).toBeGreaterThan(0);
    expect(first.atlas_context.failure_modes.length).toBeGreaterThan(0);
    expect(first.source_ids).toEqual([...first.source_ids].sort());
    expect(first.unknowns).toContain("programming language");
    expect(first.quality_requirements).toContain("unknownは最初に確認質問として返す。");
  });

  test("prefills only explicit Gallery facts and keeps environment choices unknown", () => {
    const artifacts = support();
    const item = representativeCase();
    const draft = createGalleryPromptDraft({
      item,
      datasetVersion: artifacts.data.dataset_version,
      support: artifacts,
      generatedAt: "2026-07-15T05:00:00.000Z",
    });
    const pack = createImplementationPromptPack(draft, draft.initial_form);

    expect(pack.intent).toBe(item.question);
    expect(pack.user_problem.decision_variables).toBe(`X: ${item.variable_domain}\nx: ${item.decision_variables}`);
    expect(pack.user_problem.objective).toBe(item.objective);
    expect(pack.user_problem.constraints).toBe(item.constraints);
    expect(pack.environment.programming_language).toBe("unknown");
    expect(pack.environment.preferred_libraries).toBe("unknown");
    expect(pack.environment.runtime_environment).toBe("unknown");
    expect(pack.requested_outputs).toEqual([
      "implementation_plan",
      "runnable_prototype",
      "test_validation_plan",
    ]);
    expect(pack.atlas_context.first_candidates.map((entry) => entry.entity_id)).toEqual(
      item.candidate_methods.map((entry) => entry.method_id),
    );
    expect(pack.atlas_context.first_candidates.map((entry) => entry.reasons)).toEqual(
      item.candidate_methods.map((entry) => [entry.reason]),
    );
    expect(pack.quality_requirements).toEqual(expect.arrayContaining([
      item.practical_notes,
      ...item.limitations,
    ]));
    expect(pack.atlas_context.conditional_candidates.map((entry) => entry.entity_id)).toEqual(
      item.conditional_methods.map((entry) => entry.method_id),
    );
    expect(pack.atlas_context.excluded_methods.map((entry) => entry.entity_id)).toEqual(
      item.excluded_methods.map((entry) => entry.method_id),
    );
  });

  test("rejects dataset mismatch and missing Gallery implementation artifacts", () => {
    const artifacts = support();
    const item = representativeCase();
    expect(() => createGalleryPromptDraft({
      item,
      datasetVersion: "stale",
      support: artifacts,
      generatedAt: "2026-07-15T05:00:00.000Z",
    })).toThrow(/same dataset version/u);

    expect(() => createGalleryPromptDraft({
      item: { ...item, implementation_ids: [...item.implementation_ids, "I_MISSING"] },
      datasetVersion: artifacts.data.dataset_version,
      support: artifacts,
      generatedAt: "2026-07-15T05:00:00.000Z",
    })).toThrow(/implementation is missing/u);
  });
});
