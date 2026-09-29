import { lazy, type ComponentType, type LazyExoticComponent } from "react";

/**
 * One entry per id in `src/optimization_compass/resources/explorables.json`.
 * Each figure is its own chunk, so an article without one downloads none of this code.
 */
export const EXPLORABLE_COMPONENTS: Readonly<Record<string, LazyExoticComponent<ComponentType>>> = {
  "gradient-descent-valley": lazy(() => import("./GradientDescentValley")),
  "lp-vertex-walk": lazy(() => import("./LpVertexWalk")),
  "convexity-chord": lazy(() => import("./ConvexityChord")),
};
