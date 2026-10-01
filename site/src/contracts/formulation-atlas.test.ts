import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";

import { compassNeighbors, formulationMatches, parseFormulationAtlas, relationSentence } from "./formulation-atlas";
import { parseLearningPaths, stepsAtRoute } from "./learning-paths";

const dataDirectory = resolve(__dirname, "../../public/data");
const atlas = parseFormulationAtlas(JSON.parse(readFileSync(resolve(dataDirectory, "formulation-atlas.json"), "utf8")));
const paths = parseLearningPaths(JSON.parse(readFileSync(resolve(dataDirectory, "learning-paths.json"), "utf8")));

describe("formulation atlas contract", () => {
  test("covers every formulation in exactly one family", () => {
    const members = atlas.families.flatMap((family) => family.problem_ids);
    expect(new Set(members).size).toBe(members.length);
    expect(new Set(members)).toEqual(new Set(atlas.formulations.map((item) => item.problem_id)));
  });

  test("places LP between its generalizations and special cases on the compass", () => {
    const neighbors = compassNeighbors(atlas, "PA017");
    const at = (direction: string) => neighbors
      .filter((item) => item.direction === direction)
      .map((item) => item.formulation.problem_id)
      .sort();
    expect(at("north")).toEqual(["PA018", "PA023"]);
    expect(at("south")).toEqual(["PA028"]);
    expect(at("west")).toContain("PA023");
  });

  test("states relations from the current form's point of view", () => {
    expect(relationSentence("special_case_of", true, "凸二次計画")).toBe("この形は「凸二次計画」の特別な場合です。");
    expect(relationSentence("relaxes_to", false, "MILP")).toBe("「MILP」を緩和すると、この形になります。");
  });

  test("finds forms by everyday cue words, not only by names", () => {
    const hits = atlas.formulations.filter((item) => formulationMatches(item, "外れ値")).map((item) => item.problem_id);
    expect(hits).toContain("PA034");
  });

  test("rejects relations to unknown formulations", () => {
    const raw = JSON.parse(readFileSync(resolve(dataDirectory, "formulation-atlas.json"), "utf8"));
    raw.relations.push({ from: "PA017", to: "PA999", type: "contrasts_with", note_ja: "x" });
    expect(() => parseFormulationAtlas(raw)).toThrow(/unknown formulation/u);
  });
});

describe("learning path contract", () => {
  test("every step route of a formulation targets its formulation page", () => {
    for (const path of paths.paths) {
      for (const step of path.steps.filter((item) => item.target_type === "formulation")) {
        expect(step.route).toBe(`/formulations/${step.target_id}`);
      }
    }
  });

  test("finds the path position of a page from its route", () => {
    const matches = stepsAtRoute(paths, "/formulations/PA017");
    expect(matches.map((item) => item.path.path_id)).toContain("formulation-basics");
    expect(matches.find((item) => item.path.path_id === "formulation-basics")?.step.step).toBe(2);
  });
});
