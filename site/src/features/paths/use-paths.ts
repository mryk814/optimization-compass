import { useEffect, useState } from "react";

import type { LearningPathIndex } from "../../contracts/learning-paths";
import { loadLearningPaths } from "../formulations/formulation-data";

export function usePaths() {
  const [paths, setPaths] = useState<LearningPathIndex>();
  const [error, setError] = useState<Error>();
  useEffect(() => {
    let active = true;
    void loadLearningPaths().then(
      (index) => { if (active) setPaths(index); },
      (caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught : new Error(String(caught)));
      },
    );
    return () => { active = false; };
  }, []);
  return { paths, error };
}
