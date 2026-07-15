import { useLocation, useNavigate } from "react-router-dom";

function safeFallback(pathname: string): string {
  if (pathname.startsWith("/methods/") || pathname.startsWith("/learn/")) return "/learn";
  if (pathname.startsWith("/theater/") || pathname.startsWith("/traces/")) return "/theater";
  if (pathname.startsWith("/compare/")) return "/compare";
  if (pathname.startsWith("/gallery/")) return "/gallery";
  if (pathname.startsWith("/sources/")) return "/sources";
  return "/";
}

export function SafeBackButton() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  if (pathname === "/") return null;

  const goBack = () => {
    navigate(safeFallback(pathname), { replace: true });
  };

  return (
    <nav aria-label="ページ履歴" className="page-back-row">
      <button onClick={goBack} type="button">← 戻る</button>
    </nav>
  );
}
