// Contract for data/formulation-atlas.json (ADR 0017). The exporter merges the released
// problem archetypes with data/seeds/formulation_atlas.json and the formulation articles.

export type FormulationLens = "form" | "oracle" | "application";
export type FormulationMaturity = "skeleton" | "article" | "article_with_figure";
export type FormulationRelationType =
  | "special_case_of" | "relaxes_to" | "reformulates_to" | "contrasts_with";

export interface FormulationFamily {
  family_id: string;
  lens: FormulationLens;
  title_ja: string;
  summary_ja: string;
  problem_ids: string[];
}

export interface FormulationDescriptor {
  field: string;
  label_ja: string;
  value: string;
  value_label_ja: string;
}

export interface FormulationMethod {
  method_id: string;
  name_ja: string;
  fit_level: string;
  fit_label_ja: string;
  role: "candidate" | "avoid";
}

export interface Formulation {
  problem_id: string;
  name_ja: string;
  name_en: string;
  family_id: string;
  lens: FormulationLens;
  standard_form: string;
  standard_form_html: string;
  reading_ja: string;
  cues_ja: string[];
  descriptors: FormulationDescriptor[];
  alternatives: Array<{ alternative_id: string; name_ja: string }>;
  methods: FormulationMethod[];
  content_id: string | null;
  maturity: FormulationMaturity;
  cases: Array<{ case_id: string; title_ja: string }>;
  source_ids: string[];
}

export interface FormulationRelation {
  from: string;
  to: string;
  type: FormulationRelationType;
  note_ja: string;
}

export interface FormulationAtlasIndex {
  contract_version: "1.0.0";
  dataset_version: string;
  families: FormulationFamily[];
  formulations: Formulation[];
  relations: FormulationRelation[];
  summary: { formulations: number; with_article: number; relations: number };
}

const LENSES: readonly FormulationLens[] = ["form", "oracle", "application"];
const MATURITIES: readonly FormulationMaturity[] = ["skeleton", "article", "article_with_figure"];
const RELATION_TYPES: readonly FormulationRelationType[] = [
  "special_case_of", "relaxes_to", "reformulates_to", "contrasts_with",
];

export function parseFormulationAtlas(raw: unknown): FormulationAtlasIndex {
  const data = record(raw, "formulation atlas");
  if (data.contract_version !== "1.0.0") throw new Error("Unsupported formulation atlas contract.");
  const families = array(data.families, "families").map((value, index) => {
    const item = record(value, `families[${index}]`);
    return {
      family_id: text(item.family_id, "family_id"),
      lens: oneOf(item.lens, LENSES, "lens"),
      title_ja: text(item.title_ja, "family title_ja"),
      summary_ja: text(item.summary_ja, "family summary_ja"),
      problem_ids: strings(item.problem_ids, "family problem_ids"),
    } satisfies FormulationFamily;
  });
  const formulations = array(data.formulations, "formulations").map((value, index) => {
    const item = record(value, `formulations[${index}]`);
    return {
      problem_id: text(item.problem_id, "problem_id"),
      name_ja: text(item.name_ja, "name_ja"),
      name_en: text(item.name_en, "name_en"),
      family_id: text(item.family_id, "family_id"),
      lens: oneOf(item.lens, LENSES, "lens"),
      standard_form: text(item.standard_form, "standard_form"),
      standard_form_html: text(item.standard_form_html, "standard_form_html"),
      reading_ja: text(item.reading_ja, "reading_ja"),
      cues_ja: strings(item.cues_ja, "cues_ja"),
      descriptors: array(item.descriptors, "descriptors").map((entry, position) => {
        const descriptor = record(entry, `descriptors[${position}]`);
        return {
          field: text(descriptor.field, "descriptor field"),
          label_ja: text(descriptor.label_ja, "descriptor label_ja"),
          value: text(descriptor.value, "descriptor value"),
          value_label_ja: text(descriptor.value_label_ja, "descriptor value_label_ja"),
        };
      }),
      alternatives: array(item.alternatives, "alternatives").map((entry, position) => {
        const alternative = record(entry, `alternatives[${position}]`);
        return {
          alternative_id: text(alternative.alternative_id, "alternative_id"),
          name_ja: text(alternative.name_ja, "alternative name_ja"),
        };
      }),
      methods: array(item.methods, "methods").map((entry, position) => {
        const method = record(entry, `methods[${position}]`);
        return {
          method_id: text(method.method_id, "method_id"),
          name_ja: text(method.name_ja, "method name_ja"),
          fit_level: text(method.fit_level, "fit_level"),
          fit_label_ja: text(method.fit_label_ja, "fit_label_ja"),
          role: oneOf(method.role, ["candidate", "avoid"] as const, "method role"),
        };
      }),
      content_id: item.content_id === null ? null : text(item.content_id, "content_id"),
      maturity: oneOf(item.maturity, MATURITIES, "maturity"),
      cases: array(item.cases, "cases").map((entry, position) => {
        const example = record(entry, `cases[${position}]`);
        return { case_id: text(example.case_id, "case_id"), title_ja: text(example.title_ja, "case title_ja") };
      }),
      source_ids: strings(item.source_ids, "source_ids"),
    } satisfies Formulation;
  });
  const known = new Set(formulations.map((item) => item.problem_id));
  if (known.size !== formulations.length) throw new Error("Duplicate formulation ID.");
  const relations = array(data.relations, "relations").map((value, index) => {
    const item = record(value, `relations[${index}]`);
    const relation = {
      from: text(item.from, "relation from"),
      to: text(item.to, "relation to"),
      type: oneOf(item.type, RELATION_TYPES, "relation type"),
      note_ja: text(item.note_ja, "relation note_ja"),
    } satisfies FormulationRelation;
    if (!known.has(relation.from) || !known.has(relation.to)) {
      throw new Error(`Relation references an unknown formulation: ${relation.from} → ${relation.to}`);
    }
    return relation;
  });
  const summary = record(data.summary, "summary");
  return {
    contract_version: "1.0.0",
    dataset_version: text(data.dataset_version, "dataset_version"),
    families,
    formulations,
    relations,
    summary: {
      formulations: count(summary.formulations, "summary.formulations"),
      with_article: count(summary.with_article, "summary.with_article"),
      relations: count(summary.relations, "summary.relations"),
    },
  };
}

export type CompassDirection = "north" | "south" | "east" | "west" | "contrast";

export interface CompassNeighbor {
  direction: CompassDirection;
  relation: FormulationRelation;
  formulation: Formulation;
}

/**
 * Place every relation of one formulation on a compass:
 * north = a more general form, south = a more special form,
 * east = where this form can be relaxed or rewritten to, west = forms that arrive here that way.
 */
export function compassNeighbors(index: FormulationAtlasIndex, problemId: string): CompassNeighbor[] {
  const byId = new Map(index.formulations.map((item) => [item.problem_id, item]));
  const neighbors: CompassNeighbor[] = [];
  for (const relation of index.relations) {
    const outgoing = relation.from === problemId;
    const incoming = relation.to === problemId;
    if (!outgoing && !incoming) continue;
    const other = byId.get(outgoing ? relation.to : relation.from);
    if (!other) continue;
    const direction: CompassDirection = relation.type === "contrasts_with"
      ? "contrast"
      : relation.type === "special_case_of"
        ? (outgoing ? "north" : "south")
        : (outgoing ? "east" : "west");
    neighbors.push({ direction, relation, formulation: other });
  }
  return neighbors;
}

/** One short sentence that states a relation from the point of view of the current form. */
export function relationSentence(type: FormulationRelationType, outgoing: boolean, other: string): string {
  switch (type) {
    case "special_case_of":
      return outgoing ? `この形は「${other}」の特別な場合です。` : `「${other}」は、この形の特別な場合です。`;
    case "relaxes_to":
      return outgoing ? `この形を緩和すると「${other}」になります。` : `「${other}」を緩和すると、この形になります。`;
    case "reformulates_to":
      return outgoing ? `この形は「${other}」へ書き換えられます。` : `「${other}」は、この形へ書き換えられます。`;
    case "contrasts_with":
      return `「${other}」とは、似ていても性質が違います。`;
  }
}

export function formulationMatches(item: Formulation, query: string): boolean {
  const normalized = query.trim().toLocaleLowerCase();
  if (!normalized) return true;
  return [item.problem_id, item.name_ja, item.name_en, item.reading_ja, ...item.cues_ja]
    .join(" ")
    .toLocaleLowerCase()
    .includes(normalized);
}

function record(value: unknown, owner: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error(`${owner} must be an object.`);
  return value as Record<string, unknown>;
}
function array(value: unknown, owner: string): unknown[] {
  if (!Array.isArray(value)) throw new Error(`${owner} must be an array.`);
  return value;
}
function text(value: unknown, owner: string): string {
  if (typeof value !== "string" || !value.trim()) throw new Error(`${owner} must be a non-empty string.`);
  return value;
}
function strings(value: unknown, owner: string): string[] {
  return array(value, owner).map((item, index) => text(item, `${owner}[${index}]`));
}
function count(value: unknown, owner: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) throw new Error(`${owner} must be a count.`);
  return value;
}
function oneOf<T extends string>(value: unknown, allowed: readonly T[], owner: string): T {
  if (typeof value === "string" && (allowed as readonly string[]).includes(value)) return value as T;
  throw new Error(`Unsupported ${owner}: ${String(value)}`);
}
