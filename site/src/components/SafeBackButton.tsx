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

function safeFallbackLabel(pathname: string): string {
  if (pathname.startsWith("/methods/") || pathname.startsWith("/learn/")) return "手法・概念一覧に戻る";
  if (pathname.startsWith("/theater/") || pathname.startsWith("/traces/")) return "動きの一覧に戻る";
  if (pathname.startsWith("/compare/")) return "比較一覧に戻る";
  if (pathname.startsWith("/gallery/")) return "Case一覧に戻る";
  if (pathname.startsWith("/sources/")) return "根拠一覧に戻る";
  return "ホームに戻る";
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
    <nav aria-label="関連する入口へ戻る" className="page-back-row">
      <button onClick={goBack} type="button">
        {caseDestination?.ok ? "← このCaseへ戻る" : `← ${safeFallbackLabel(pathname)}`}
      </button>
    </nav>
  );
}
