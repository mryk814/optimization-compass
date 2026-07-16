import { describe, expect, test } from "vitest";
import rawPrimer from "../../public/data/formulation-primer.json";
import { parseFormulationPrimerIndex } from "./formulation-primer";

describe("formulation primer contract", () => {
  test("parses generated canonical terms and all twelve diagnosis mappings", () => {
    const primer = parseFormulationPrimerIndex(rawPrimer);
    expect(primer.fields.map((field) => field.field_id)).toContain("variable_domain");
    expect(primer.diagnosis_mappings).toHaveLength(12);
    expect(primer.terms.some((term) => term.term_en === "Categorical variable")).toBe(true);
  });

  test("rejects duplicate and missing term references", () => {
    const duplicate = structuredClone(rawPrimer);
    duplicate.fields[0].term_ids.push(duplicate.fields[0].term_ids[0]);
    expect(() => parseFormulationPrimerIndex(duplicate)).toThrow(/unique/u);
    const missing = structuredClone(rawPrimer);
    missing.fields[0].term_ids[0] = "MISSING";
    expect(() => parseFormulationPrimerIndex(missing)).toThrow(/unknown terms/u);
  });
});
