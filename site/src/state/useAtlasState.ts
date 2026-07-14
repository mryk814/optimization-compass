import { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import {
  decodeAtlasState,
  encodeAtlasState,
  type AtlasCompatibilityCatalog,
  type AtlasStateV1,
} from "./atlas-state";

export interface AtlasStateController {
  state: AtlasStateV1;
  warnings: readonly string[];
  error?: Error;
  setState(
    update: (current: AtlasStateV1) => AtlasStateV1,
    options?: { replace?: boolean },
  ): void;
  reset(): void;
}

interface DecodedControllerState {
  state: AtlasStateV1;
  warnings: string[];
  error?: Error;
}

function initialState(catalog: AtlasCompatibilityCatalog): AtlasStateV1 {
  return {
    stateVersion: 1,
    datasetVersion: catalog.datasetVersion,
    viewId: catalog.viewId,
    viewVersion: catalog.viewVersion,
    answers: {},
  };
}

export function useAtlasState(catalog: AtlasCompatibilityCatalog): AtlasStateController {
  const location = useLocation();
  const navigate = useNavigate();
  const [migrationWarnings, setMigrationWarnings] = useState<readonly string[]>([]);
  const [mutationError, setMutationError] = useState<Error>();
  const token = useMemo(() => new URLSearchParams(location.search).get("state"), [location.search]);

  const decoded = useMemo<DecodedControllerState>(() => {
    if (token === null) return { state: initialState(catalog), warnings: [] as string[] };
    try {
      return decodeAtlasState(token, catalog);
    } catch (caught) {
      return {
        state: initialState(catalog),
        warnings: [] as string[],
        error: caught instanceof Error ? caught : new Error(String(caught)),
      };
    }
  }, [catalog, token]);

  const navigateWithToken = useCallback(
    (nextToken: string | undefined, replace: boolean) => {
      const params = new URLSearchParams(location.search);
      if (nextToken === undefined) params.delete("state");
      else params.set("state", nextToken);
      const search = params.toString();
      navigate({ pathname: location.pathname, search: search ? `?${search}` : "" }, { replace });
    },
    [location.pathname, location.search, navigate],
  );

  useEffect(() => {
    if (decoded.error || decoded.warnings.length === 0 || token === null) return;
    const canonicalToken = encodeAtlasState(decoded.state);
    setMigrationWarnings(decoded.warnings);
    if (canonicalToken !== token) navigateWithToken(canonicalToken, true);
  }, [decoded, navigateWithToken, token]);

  const setState = useCallback<AtlasStateController["setState"]>(
    (update, options) => {
      const next = update(decoded.state);
      setMigrationWarnings([]);
      setMutationError(undefined);
      try {
        navigateWithToken(encodeAtlasState(next), options?.replace ?? false);
      } catch (caught) {
        setMutationError(caught instanceof Error ? caught : new Error(String(caught)));
      }
    },
    [decoded.state, navigateWithToken],
  );

  const reset = useCallback(() => {
    setMigrationWarnings([]);
    setMutationError(undefined);
    navigateWithToken(undefined, true);
  }, [navigateWithToken]);

  return {
    state: decoded.state,
    warnings: decoded.warnings.length > 0 ? decoded.warnings : migrationWarnings,
    error: mutationError ?? decoded.error,
    setState,
    reset,
  };
}
