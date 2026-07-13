import { useCallback, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { encodeAtlasState, type AtlasStateV1 } from "./atlas-state";

export type AtlasNavigationResult =
  | { ok: true; to: { pathname: string; search: string } }
  | { ok: false; error: Error };

export function buildAtlasNavigation(
  pathname: string,
  currentSearch: string,
  state: AtlasStateV1,
): AtlasNavigationResult {
  try {
    const token = encodeAtlasState(state);
    const params = new URLSearchParams(currentSearch);
    params.set("state", token);
    const search = params.toString();
    return { ok: true, to: { pathname, search: search ? `?${search}` : "" } };
  } catch (caught) {
    return {
      ok: false,
      error: caught instanceof Error ? caught : new Error(String(caught)),
    };
  }
}

export function useAtlasNavigation(): {
  error?: Error;
  navigateWithState(pathname: string, state: AtlasStateV1, options?: { replace?: boolean }): void;
} {
  const location = useLocation();
  const navigate = useNavigate();
  const [error, setError] = useState<Error>();
  const navigateWithState = useCallback(
    (pathname: string, state: AtlasStateV1, options?: { replace?: boolean }) => {
      const result = buildAtlasNavigation(pathname, location.search, state);
      if (!result.ok) {
        setError(result.error);
        return;
      }
      setError(undefined);
      navigate(result.to, { replace: options?.replace ?? false });
    },
    [location.search, navigate],
  );
  return { error, navigateWithState };
}
