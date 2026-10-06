import { useEffect, useState } from "react";

import type { GalleryCase } from "../contracts/gallery";
import { loadGalleryCases } from "./CaseSignatureStrip";
import { buildMethodLens, type LensCatalog } from "./method-lens";
import { ProblemSignature } from "./ProblemSignature";
import { blankSignature, buildSignature, caseAnswers } from "./signature";

/** Gallery cases by ID, fetched once and shared by every glyph on the page. */
export function useGalleryCases(enabled = true): ReadonlyMap<string, GalleryCase> | undefined {
  const [cases, setCases] = useState<ReadonlyMap<string, GalleryCase>>();
  useEffect(() => {
    if (!enabled) return undefined;
    let active = true;
    void loadGalleryCases().then(
      (items) => { if (active) setCases(new Map(items.map((item) => [item.case_id, item]))); },
      () => undefined,
    );
    return () => { active = false; };
  }, [enabled]);
  return cases;
}

/** A Case's problem signature as a card glyph, wherever the Case is listed. */
export function CaseSignatureGlyph({ item }: { item: GalleryCase }) {
  return <ProblemSignature axes={buildSignature(caseAnswers(item.question_answers))} label={`${item.title_ja}の問題の署名`} size="compact" />;
}

/**
 * A method's lens with no problem placed on it, as a card glyph: which axes it reads and which
 * values support or exclude it. Nothing is drawn when no rule or predicate reaches the method.
 */
export function MethodLensGlyph({ methodId, catalog, label }: { methodId: string; catalog: LensCatalog; label: string }) {
  const lens = buildMethodLens(methodId, {}, catalog);
  if (lens.readAxisCount === 0) return null;
  return <ProblemSignature axes={blankSignature()} label={`${label}が読む軸`} lens={lens} size="compact" />;
}
