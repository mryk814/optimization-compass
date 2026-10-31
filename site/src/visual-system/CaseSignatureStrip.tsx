import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { parseGalleryIndex, type GalleryCase } from "../contracts/gallery";
import { findEntity } from "../contracts/entity-links";
import { siteBaseUrl } from "../data/base-url";
import { useEntityLinks } from "../state/entity-links";
import { DispositionMark } from "./DispositionMark";
import { ProblemSignature } from "./ProblemSignature";
import { buildSignature, caseAnswers } from "./signature";

let galleryCases: Promise<GalleryCase[]> | undefined;

export function loadGalleryCases(): Promise<GalleryCase[]> {
  galleryCases ??= fetch(`${siteBaseUrl()}data/gallery.json`)
    .then((response) => {
      if (!response.ok) throw new Error(`Gallery request failed (${response.status}).`);
      return response.json() as Promise<unknown>;
    })
    .then((raw) => parseGalleryIndex(raw).cases)
    .catch((error: unknown) => {
      galleryCases = undefined;
      throw error;
    });
  return galleryCases;
}

/**
 * "Which problem is this happening on?" — the Case's signature and its candidate / excluded
 * marks, placed above a comparison or a run so the reader keeps the problem in view.
 */
export function CaseSignatureStrip({ caseId, children }: { caseId: string; children?: React.ReactNode }) {
  const [item, setItem] = useState<GalleryCase | null>();
  const links = useEntityLinks();
  const label = (id: string) => (links.status === "ready" ? findEntity(links.index, "method", id)?.label : undefined) ?? id;
  useEffect(() => {
    let active = true;
    void loadGalleryCases().then(
      (cases) => { if (active) setItem(cases.find((entry) => entry.case_id === caseId) ?? null); },
      () => { if (active) setItem(null); },
    );
    return () => { active = false; };
  }, [caseId]);
  if (!item) return null;
  return (
    <aside className="vs-case-strip" aria-label="この比較の問題">
      <ProblemSignature axes={buildSignature(caseAnswers(item.question_answers))} size="compact" />
      <div>
        <p className="eyebrow">この比較の問題</p>
        <Link to={`/gallery/${item.case_id}`}>{item.title_ja}</Link>
        <ul className="gallery-card-dispositions">
          {item.candidate_methods.map((entry) => <li key={entry.method_id}><DispositionMark kind="candidate" label={false} />{label(entry.method_id)}</li>)}
          {item.conditional_methods.map((entry) => <li key={entry.method_id}><DispositionMark kind="conditional" label={false} />{label(entry.method_id)}</li>)}
          {item.excluded_methods.map((entry) => <li key={entry.method_id}><DispositionMark kind="excluded" label={false} />{label(entry.method_id)}</li>)}
        </ul>
      </div>
      {children}
    </aside>
  );
}
