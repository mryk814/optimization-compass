import { useLocation, useNavigate } from "react-router-dom";

import { buildAtlasNavigation } from "../state/atlas-navigation";
import { atlasStateFromSearch } from "../state/journey-navigation";

function safeFallback(pathname: string): string {
  if (pathname.startsWith("/methods/") || pathname.startsWith("/learn/")) return "/learn";
  if (pathname.startsWith("/theater/") || pathname.startsWith("/traces/")) return "/theater";
  if (pathname.startsWith("/compare/")) return "/compare";
  if (pathname.startsWith("/gallery/")) return "/gallery";
  if (pathname.startsWith("/sources/")) return "/sources";
  return "/";
}

export function SafeBackButton() {
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  if (pathname === "/") return null;

  const state = atlasStateFromSearch(search);
  const caseDestination = state?.journey
    ? buildAtlasNavigation(`/gallery/${state.journey.caseId}`, search, state)
    : undefined;

  const goBack = () => {
    navigate(caseDestination?.ok ? caseDestination.to : safeFallback(pathname), { replace: true });
  };

  return (
    <nav aria-label="ページ履歴" className="page-back-row">
      <button onClick={goBack} type="button">
        {caseDestination?.ok ? "← このCaseへ戻る" : "← 戻る"}
      </button>
    </nav>
  );
}
