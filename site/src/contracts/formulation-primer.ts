export interface PrimerTerm {
  term_id: string;
  term_ja: string;
  term_en: string;
  definition: string;
  common_confusion: string;
}

export interface FormulationField {
  field_id: string;
  symbol: string;
  label_ja: string;
  label_en: string;
  beginner_description: string;
  term_ids: string[];
}

export interface FormulationPrimerIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  generated_at: string;
  formula_aria_label_ja: string;
  fields: FormulationField[];
  terminology_groups: { group_id: string; title_ja: string; term_ids: string[] }[];
  diagnosis_mappings: { question_id: string; field_id: string; cue_ja: string; term_ids: string[] }[];
  terms: PrimerTerm[];
}

export function parseFormulationPrimerIndex(raw: unknown): FormulationPrimerIndex {
  const data = record(raw, "formulation primer");
  exactKeys(data, ["contract_version", "dataset_version", "generated_at", "formula_aria_label_ja", "fields", "terminology_groups", "diagnosis_mappings", "terms"], "formulation primer");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported formulation primer contract.");
  const terms = array(data.terms, "terms").map((value, index) => {
    const item = record(value, `terms[${index}]`);
    exactKeys(item, ["term_id", "term_ja", "term_en", "definition", "common_confusion"], `terms[${index}]`);
    return { term_id: text(item.term_id, "term_id"), term_ja: text(item.term_ja, "term_ja"), term_en: text(item.term_en, "term_en"), definition: text(item.definition, "definition"), common_confusion: text(item.common_confusion, "common_confusion") };
  });
  unique(terms.map((term) => term.term_id), "term IDs");
  const termIds = new Set(terms.map((term) => term.term_id));
  const fields = array(data.fields, "fields").map((value, index) => {
    const item = record(value, `fields[${index}]`);
    exactKeys(item, ["field_id", "symbol", "label_ja", "label_en", "beginner_description", "term_ids"], `fields[${index}]`);
    return { field_id: text(item.field_id, "field_id"), symbol: text(item.symbol, "symbol"), label_ja: text(item.label_ja, "label_ja"), label_en: text(item.label_en, "label_en"), beginner_description: text(item.beginner_description, "beginner_description"), term_ids: references(item.term_ids, "field term_ids", termIds) };
  });
  unique(fields.map((field) => field.field_id), "field IDs");
  const fieldIds = new Set(fields.map((field) => field.field_id));
  const terminologyGroups = array(data.terminology_groups, "terminology_groups").map((value, index) => {
    const item = record(value, `terminology_groups[${index}]`);
    exactKeys(item, ["group_id", "title_ja", "term_ids"], `terminology_groups[${index}]`);
    return { group_id: text(item.group_id, "group_id"), title_ja: text(item.title_ja, "title_ja"), term_ids: references(item.term_ids, "group term_ids", termIds) };
  });
  const diagnosisMappings = array(data.diagnosis_mappings, "diagnosis_mappings").map((value, index) => {
    const item = record(value, `diagnosis_mappings[${index}]`);
    exactKeys(item, ["question_id", "field_id", "cue_ja", "term_ids"], `diagnosis_mappings[${index}]`);
    const fieldId = text(item.field_id, "field_id");
    if (!fieldIds.has(fieldId)) throw new Error(`Unknown diagnosis field: ${fieldId}.`);
    return { question_id: text(item.question_id, "question_id"), field_id: fieldId, cue_ja: text(item.cue_ja, "cue_ja"), term_ids: references(item.term_ids, "diagnosis term_ids", termIds) };
  });
  unique(diagnosisMappings.map((mapping) => mapping.question_id), "diagnosis question IDs");
  return { contract_version: "1.0.0", dataset_version: text(data.dataset_version, "dataset_version"), generated_at: text(data.generated_at, "generated_at"), formula_aria_label_ja: text(data.formula_aria_label_ja, "formula_aria_label_ja"), fields, terminology_groups: terminologyGroups, diagnosis_mappings: diagnosisMappings, terms };
}

function references(value: unknown, field: string, known: ReadonlySet<string>): string[] { const ids = array(value, field).map((item, index) => text(item, `${field}[${index}]`)); unique(ids, field); const missing = ids.filter((id) => !known.has(id)); if (missing.length > 0) throw new Error(`${field} has unknown terms: ${missing.join(", ")}.`); return ids; }
function unique(values: string[], field: string): void { if (new Set(values).size !== values.length) throw new Error(`${field} must be unique.`); }
function record(value: unknown, field: string): Record<string, unknown> { if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${field} must be an object.`); return value as Record<string, unknown>; }
function array(value: unknown, field: string): unknown[] { if (!Array.isArray(value)) throw new Error(`${field} must be an array.`); return value; }
function text(value: unknown, field: string): string { if (typeof value !== "string" || !value.trim()) throw new Error(`${field} must be non-empty.`); return value; }
function exactKeys(value: Record<string, unknown>, expected: string[], field: string): void { const keys = new Set(expected); const unknown = Object.keys(value).filter((key) => !keys.has(key)); const missing = expected.filter((key) => !Object.hasOwn(value, key)); if (unknown.length) throw new Error(`${field} has unknown fields: ${unknown.join(", ")}.`); if (missing.length) throw new Error(`${field} is missing fields: ${missing.join(", ")}.`); }
