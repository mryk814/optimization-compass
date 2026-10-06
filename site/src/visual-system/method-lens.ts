/**
 * Method Lens: which signature axes a method reads, and what each axis says about it for one
 * problem. Derived only from canonical rules and atomic predicates on the same features the
 * diagnosis questions map to, so it explains a disposition instead of inventing one.
 *
 * The lens never assigns a candidate/excluded band itself. The band comes from the Case
 * (editorial, sourced) or from `recommend()`; the lens shows where on the axes it comes from.
 */
import type { SitePredicate, SiteQuestion, SiteRule } from "../contracts/site-data";
import { SIGNATURE_AXES, shortValueLabel, type SignatureAnswer } from "./signature";

/**
 * - supports: a promote rule matches this answer, or an assumption predicate is satisfied.
 * - blocks: an exclude rule or incompatibility predicate matches, or an assumption is violated.
 * - open: the method reads this axis, but the answer is missing or unknown.
 * - silent: the method reads this axis, and this answer triggers nothing.
 * - unread: no canonical rule or predicate connects this method to the axis.
 */
export type LensAxisStatus = "supports" | "blocks" | "open" | "silent" | "unread";

export interface LensEvidence {
  kind: "promote_rule" | "exclude_rule" | "assumption" | "incompatibility";
  id: string;
  text: string;
  sourceIds: readonly string[];
}

export interface LensAxis {
  questionId: string;
  name: string;
  status: LensAxisStatus;
  /** What fired (or would need checking) on this axis. */
  evidence: LensEvidence[];
  /** Values on this axis under which a promote rule fires or the assumption holds. */
  flipValues: string[];
  /** Values on this axis that an exclude rule or an incompatibility predicate names. */
  blockValues: string[];
  /** A rule supports while an atomic predicate disagrees: shown, never silently resolved. */
  conflict: boolean;
}

export interface MethodLens {
  methodId: string;
  axes: LensAxis[];
  readAxisCount: number;
  blockingAxes: LensAxis[];
  supportingAxes: LensAxis[];
  openAxes: LensAxis[];
}

export interface LensCatalog {
  questions: readonly Pick<SiteQuestion, "question_id" | "mapped_feature_id">[];
  rules: readonly SiteRule[];
  predicates: readonly SitePredicate[];
}

function predicateValues(predicate: SitePredicate): string[] | undefined {
  const { value } = predicate;
  if (typeof value === "string") return [value];
  if (Array.isArray(value) && value.every((item) => typeof item === "string")) return value as string[];
  return undefined;
}

/** Whether the predicate's condition holds for the answered values (any value matches). */
function predicateMatches(predicate: SitePredicate, values: readonly string[]): boolean | undefined {
  const expected = predicateValues(predicate);
  if (!expected) return undefined;
  const hit = values.some((value) => expected.includes(value));
  switch (predicate.operator) {
    case "eq":
    case "in":
    case "contains":
      return hit;
    case "neq":
    case "not_in":
      return !hit;
    default:
      return undefined;
  }
}

export function buildMethodLens(
  methodId: string,
  answers: Readonly<Record<string, SignatureAnswer | undefined>>,
  catalog: LensCatalog,
): MethodLens {
  const featureByQuestion = new Map(catalog.questions.map((question) => [question.question_id, question.mapped_feature_id]));
  const axes = SIGNATURE_AXES.map((axis): LensAxis => {
    const feature = featureByQuestion.get(axis.questionId);
    const rules = catalog.rules.filter((rule) => (
      rule.question_id === axis.questionId
      && rule.action_target_ids.includes(methodId)
      && (rule.action_type === "promote_method" || rule.action_type === "exclude_method")
    ));
    const predicates = catalog.predicates.filter((predicate) => (
      predicate.subject_id === methodId
      && predicate.feature_id === feature
      && (predicate.predicate_kind === "assumption" || predicate.predicate_kind === "incompatibility")
    ));
    const flipValues = new Set<string>();
    rules.filter((rule) => rule.action_type === "promote_method").forEach((rule) => flipValues.add(rule.answer_condition));
    predicates
      .filter((predicate) => predicate.predicate_kind === "assumption" && (predicate.operator === "eq" || predicate.operator === "in"))
      .forEach((predicate) => predicateValues(predicate)?.forEach((value) => flipValues.add(value)));

    const blockValues = new Set<string>();
    rules.filter((rule) => rule.action_type === "exclude_method").forEach((rule) => blockValues.add(rule.answer_condition));
    predicates
      .filter((predicate) => predicate.predicate_kind === "incompatibility" && (predicate.operator === "eq" || predicate.operator === "in"))
      .forEach((predicate) => predicateValues(predicate)?.forEach((value) => blockValues.add(value)));
    const base = { questionId: axis.questionId, name: axis.name, flipValues: [...flipValues], blockValues: [...blockValues] };
    if (rules.length === 0 && predicates.length === 0) {
      return { ...base, status: "unread", evidence: [], conflict: false };
    }
    const answer = answers[axis.questionId];
    const values = answer && answer.status === "answered" ? answer.values.filter((value) => value !== "unknown") : [];
    if (answer?.status === "not_applicable") {
      return { ...base, status: "silent", evidence: [], conflict: false };
    }
    if (values.length === 0) {
      // Open: list what would decide this axis, so the reader sees what to find out.
      const evidence: LensEvidence[] = predicates.map((predicate) => ({
        kind: predicate.predicate_kind === "assumption" ? "assumption" : "incompatibility",
        id: predicate.predicate_id,
        text: predicateText(axis.questionId, predicate),
        sourceIds: predicate.source_ids,
      }));
      return { ...base, status: "open", evidence, conflict: false };
    }

    const evidence: LensEvidence[] = [];
    let supports = false;
    let blocks = false;
    let predicateBlocks = false;
    rules.forEach((rule) => {
      if (!values.includes(rule.answer_condition)) return;
      if (rule.action_type === "promote_method") {
        supports = true;
        evidence.push({ kind: "promote_rule", id: rule.rule_id, text: rule.explanation, sourceIds: rule.source_ids });
      } else {
        blocks = true;
        evidence.push({ kind: "exclude_rule", id: rule.rule_id, text: rule.explanation, sourceIds: rule.source_ids });
      }
    });
    predicates.forEach((predicate) => {
      const matches = predicateMatches(predicate, values);
      if (matches === undefined) return;
      const violated = predicate.predicate_kind === "assumption" ? !matches : matches;
      if (violated) {
        predicateBlocks = true;
        evidence.push({
          kind: predicate.predicate_kind === "assumption" ? "assumption" : "incompatibility",
          id: predicate.predicate_id,
          text: predicateText(axis.questionId, predicate),
          sourceIds: predicate.source_ids,
        });
      } else if (predicate.predicate_kind === "assumption") {
        supports = true;
        evidence.push({ kind: "assumption", id: predicate.predicate_id, text: predicateText(axis.questionId, predicate), sourceIds: predicate.source_ids });
      }
    });
    const blocked = blocks || predicateBlocks;
    return {
      ...base,
      status: blocked ? "blocks" : supports ? "supports" : "silent",
      evidence,
      conflict: predicateBlocks && supports && !blocks,
    };
  });
  return {
    methodId,
    axes,
    readAxisCount: axes.filter((axis) => axis.status !== "unread").length,
    blockingAxes: axes.filter((axis) => axis.status === "blocks"),
    supportingAxes: axes.filter((axis) => axis.status === "supports"),
    openAxes: axes.filter((axis) => axis.status === "open"),
  };
}

function predicateText(questionId: string, predicate: SitePredicate): string {
  const values = (predicateValues(predicate) ?? []).map((value) => shortValueLabel(questionId, value)).join("・");
  if (predicate.predicate_kind === "assumption") {
    const negated = predicate.operator === "neq" || predicate.operator === "not_in";
    return negated ? `前提: ${values} ではない` : `前提: ${values}`;
  }
  return `非互換: ${values}`;
}

export function flipText(axis: LensAxis): string | undefined {
  if (axis.flipValues.length === 0) return undefined;
  const labels = axis.flipValues.map((value) => shortValueLabel(axis.questionId, value)).join("・");
  return `${axis.name}が「${labels}」なら支える規則・前提がある`;
}
