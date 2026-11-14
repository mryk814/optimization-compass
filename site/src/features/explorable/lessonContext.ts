import { createContext } from "react";

import type { SceneBeat } from "./scene";

/**
 * What an article's lesson tells the figure inside it (see `Lesson.tsx`). `useSceneTour` reads
 * this, so a figure needs no lesson-specific code: it keeps drawing from `tour.values`.
 */
export interface LessonDrive {
  /** One beat per step of the lesson, with every param of the figure set. */
  beats: readonly SceneBeat[];
  /** The step the reader is on. */
  index: number;
  /** Seconds since that step was entered, in [0, its duration]. */
  local: number;
  /** True once the reader has taken over the controls. */
  free: boolean;
}

export const LessonContext = createContext<LessonDrive | null>(null);
