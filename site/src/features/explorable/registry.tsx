import { lazy, type ComponentType, type LazyExoticComponent } from "react";

/** `./figures/<id>/<file>` → `<id>`: a figure's folder name is the id articles use. */
export function figureIdOf(path: string): string {
  const match = /^\.\/figures\/([^/]+)\//u.exec(path);
  if (!match) throw new Error(`not inside a figure folder: ${path}`);
  return match[1];
}

const loaders = import.meta.glob<{ default: ComponentType }>("./figures/*/Figure.tsx");

/**
 * One entry per figure folder, found by its `Figure.tsx`; adding a figure needs no edit here.
 * Each figure is its own chunk, so an article without one downloads none of this code.
 */
export const EXPLORABLE_COMPONENTS: Readonly<Record<string, LazyExoticComponent<ComponentType>>> = Object.fromEntries(
  Object.entries(loaders).map(([path, load]) => [figureIdOf(path), lazy(load)]),
);
