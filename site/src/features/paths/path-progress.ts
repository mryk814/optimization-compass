import { useCallback, useEffect, useState } from "react";

// Progress is a per-viewer convenience: it lives only in this browser and the site must work
// without it (private windows, blocked storage).
const PROGRESS_KEY = "oc.path-progress.v1";
const ACTIVE_KEY = "oc.active-path.v1";
const CHANGE_EVENT = "oc:path-progress";

type ProgressMap = Record<string, string[]>;
let sessionProgress: ProgressMap = {};
let sessionOnly = false;

function readProgress(): ProgressMap {
  if (sessionOnly) return sessionProgress;
  try {
    const raw = window.localStorage.getItem(PROGRESS_KEY);
    if (!raw) return {};
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) return {};
    return Object.fromEntries(
      Object.entries(parsed).filter(
        (entry): entry is [string, string[]] => Array.isArray(entry[1])
          && entry[1].every((item) => typeof item === "string"),
      ),
    );
  } catch {
    return sessionProgress;
  }
}

function writeProgress(progress: ProgressMap) {
  sessionProgress = progress;
  try {
    window.localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
  } catch {
    sessionOnly = true;
    // Storage may be unavailable; progress then lasts only for this page view.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function readActivePath(): string | undefined {
  try {
    return window.localStorage.getItem(ACTIVE_KEY) ?? undefined;
  } catch {
    return undefined;
  }
}

export function rememberActivePath(pathId: string) {
  try {
    window.localStorage.setItem(ACTIVE_KEY, pathId);
  } catch {
    // Not remembering the active path only changes which path is shown first.
  }
}

/** Completed step keys per path, kept in sync across components on the page. */
export function usePathProgress() {
  const [progress, setProgress] = useState<ProgressMap>(() => readProgress());
  useEffect(() => {
    const sync = () => setProgress(readProgress());
    window.addEventListener(CHANGE_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(CHANGE_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);
  const isDone = useCallback(
    (pathId: string, key: string) => (progress[pathId] ?? []).includes(key),
    [progress],
  );
  const setDone = useCallback((pathId: string, key: string, done: boolean) => {
    const current = readProgress();
    const keys = new Set(current[pathId] ?? []);
    if (done) keys.add(key);
    else keys.delete(key);
    writeProgress({ ...current, [pathId]: [...keys].sort() });
  }, []);
  const doneCount = useCallback(
    (pathId: string) => (progress[pathId] ?? []).length,
    [progress],
  );
  return { isDone, setDone, doneCount };
}
