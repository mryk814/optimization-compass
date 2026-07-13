export type AtlasAnswer =
  | { status: "answered"; values: string[] }
  | { status: "unknown"; values: ["unknown"] }
  | { status: "not_applicable"; values: [] };

export interface AtlasStateV1 {
  stateVersion: 1;
  datasetVersion: string;
  viewId: string;
  viewVersion: string;
  selectedNodeId?: string;
  answers: Record<string, AtlasAnswer>;
}

export interface AtlasCompatibilityCatalog {
  datasetVersion: string;
  viewId: string;
  viewVersion: string;
  nodeIds: ReadonlySet<string>;
  questions: Readonly<
    Record<
      string,
      {
        answerType: "single_choice" | "multi_choice";
        allowedAnswers: readonly string[];
      }
    >
  >;
}

export const ATLAS_STATE_TOKEN_MAX_LENGTH = 1800;

export class AtlasStateUrlTooLongError extends Error {
  readonly tokenLength: number;
  readonly maxLength = ATLAS_STATE_TOKEN_MAX_LENGTH;

  constructor(tokenLength: number) {
    super(
      `AtlasState URL token is ${tokenLength} characters; the maximum is ${ATLAS_STATE_TOKEN_MAX_LENGTH}.`,
    );
    this.name = "AtlasStateUrlTooLongError";
    this.tokenLength = tokenLength;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireNonEmptyString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`AtlasState ${field} is required and must be a string.`);
  }
  if (value.trim().length === 0) {
    throw new Error(`AtlasState ${field} is empty.`);
  }
  return value;
}

function validateAnswer(value: unknown, questionId: string): AtlasAnswer {
  if (!isRecord(value) || !Array.isArray(value.values)) {
    throw new Error(`AtlasState answer "${questionId}" has invalid status/values.`);
  }

  const values = value.values;
  if (!values.every((answerValue) => typeof answerValue === "string")) {
    throw new Error(`AtlasState answer "${questionId}" has invalid values.`);
  }
  values.forEach((answerValue) => requireNonEmptyString(answerValue, "answer ID"));

  if (value.status === "answered") {
    if (values.length === 0 || values.includes("unknown")) {
      throw new Error(`AtlasState answer "${questionId}" has invalid status/values.`);
    }
    return { status: "answered", values: [...values] };
  }

  if (value.status === "unknown") {
    if (values.length !== 1 || values[0] !== "unknown") {
      throw new Error(`AtlasState answer "${questionId}" has invalid status/values.`);
    }
    return { status: "unknown", values: ["unknown"] };
  }

  if (value.status === "not_applicable") {
    if (values.length !== 0) {
      throw new Error(`AtlasState answer "${questionId}" has invalid status/values.`);
    }
    return { status: "not_applicable", values: [] };
  }

  throw new Error(`AtlasState answer "${questionId}" has invalid status "${String(value.status)}".`);
}

function validateStateShape(value: unknown): AtlasStateV1 {
  if (!isRecord(value)) {
    throw new Error("AtlasState payload must be a JSON object.");
  }
  if (value.stateVersion !== 1) {
    throw new Error(`AtlasState stateVersion "${String(value.stateVersion)}" is not supported.`);
  }

  const datasetVersion = requireNonEmptyString(value.datasetVersion, "datasetVersion");
  const viewId = requireNonEmptyString(value.viewId, "viewId");
  const viewVersion = requireNonEmptyString(value.viewVersion, "viewVersion");
  const rawAnswers = value.answers;
  if (!isRecord(rawAnswers)) {
    throw new Error("AtlasState answers is required and must be an object.");
  }

  const answerEntries = Object.keys(rawAnswers)
    .sort()
    .map((questionId) => {
      requireNonEmptyString(questionId, "question ID");
      return [questionId, validateAnswer(rawAnswers[questionId], questionId)] as const;
    });

  const state: AtlasStateV1 = {
    stateVersion: 1,
    datasetVersion,
    viewId,
    viewVersion,
    answers: Object.fromEntries(answerEntries),
  };
  if (value.selectedNodeId !== undefined) {
    state.selectedNodeId = requireNonEmptyString(value.selectedNodeId, "selectedNodeId");
  }
  return state;
}

function encodeUtf8Base64Url(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/u, "");
}

function decodeUtf8Base64Url(token: string): string {
  if (
    token.length === 0 ||
    token.length % 4 === 1 ||
    !/^[A-Za-z0-9_-]+$/u.test(token)
  ) {
    throw new Error("AtlasState token is malformed base64url.");
  }

  try {
    const base64 = token.replaceAll("-", "+").replaceAll("_", "/");
    const binary = atob(base64 + "=".repeat((4 - (base64.length % 4)) % 4));
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    const decoded = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    if (encodeUtf8Base64Url(decoded) !== token) {
      throw new Error("non-canonical base64url");
    }
    return decoded;
  } catch (error) {
    throw new Error("AtlasState token is malformed base64url or UTF-8.", { cause: error });
  }
}

function canonicalizeForEncoding(state: AtlasStateV1): AtlasStateV1 {
  const validated = validateStateShape(state);
  const answerEntries = Object.entries(validated.answers).map(([questionId, answer]) => {
    if (answer.status !== "answered") {
      return [questionId, answer] as const;
    }
    return [questionId, { status: "answered" as const, values: [...answer.values].sort() }] as const;
  });
  return { ...validated, answers: Object.fromEntries(answerEntries) };
}

export function encodeAtlasState(state: AtlasStateV1): string {
  const canonical = canonicalizeForEncoding(state);
  const token = encodeUtf8Base64Url(JSON.stringify(canonical));
  if (token.length > ATLAS_STATE_TOKEN_MAX_LENGTH) {
    throw new AtlasStateUrlTooLongError(token.length);
  }
  return token;
}

export function decodeAtlasState(
  token: string,
  catalog: AtlasCompatibilityCatalog,
): { state: AtlasStateV1; warnings: string[] } {
  if (token.length > ATLAS_STATE_TOKEN_MAX_LENGTH) {
    throw new AtlasStateUrlTooLongError(token.length);
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(decodeUtf8Base64Url(token)) as unknown;
  } catch (error) {
    if (error instanceof Error && error.message.startsWith("AtlasState")) {
      throw error;
    }
    throw new Error("AtlasState token contains malformed JSON.", { cause: error });
  }

  const decoded = validateStateShape(parsed);
  const catalogDatasetVersion = requireNonEmptyString(
    catalog.datasetVersion,
    "catalog datasetVersion",
  );
  const catalogViewId = requireNonEmptyString(catalog.viewId, "catalog viewId");
  const catalogViewVersion = requireNonEmptyString(catalog.viewVersion, "catalog viewVersion");
  if (decoded.viewId !== catalogViewId) {
    throw new Error(
      `AtlasState viewId "${decoded.viewId}" is incompatible with catalog viewId "${catalogViewId}".`,
    );
  }

  const warnings: string[] = [];
  if (decoded.datasetVersion !== catalogDatasetVersion) {
    warnings.push(
      `データセット版を「${decoded.datasetVersion}」から「${catalogDatasetVersion}」へ更新しました。`,
    );
  }
  if (decoded.viewVersion !== catalogViewVersion) {
    warnings.push(
      `ビュー版を「${decoded.viewVersion}」から「${catalogViewVersion}」へ更新しました。`,
    );
  }

  const validAnswerEntries: Array<readonly [string, AtlasAnswer]> = [];
  for (const [questionId, answer] of Object.entries(decoded.answers)) {
    if (!Object.prototype.hasOwnProperty.call(catalog.questions, questionId)) {
      warnings.push(
        `質問「${questionId}」は現在のデータセットに存在しないため除外しました。`,
      );
      continue;
    }

    const question = catalog.questions[questionId];
    if (answer.status === "unknown") {
      if (!question.allowedAnswers.includes("unknown")) {
        warnings.push(
          `質問「${questionId}」の回答「unknown」は現在の選択肢にないため除外しました。`,
        );
        continue;
      }
      validAnswerEntries.push([questionId, answer]);
      continue;
    }
    if (answer.status === "not_applicable") {
      validAnswerEntries.push([questionId, answer]);
      continue;
    }
    if (question.answerType === "single_choice" && answer.values.length !== 1) {
      throw new Error(
        `AtlasState single_choice answer "${questionId}" must contain exactly one value.`,
      );
    }

    const allowedAnswers = new Set(question.allowedAnswers);
    const validValues = answer.values.filter((answerValue) => {
      if (allowedAnswers.has(answerValue)) {
        return true;
      }
      warnings.push(
        `質問「${questionId}」の回答「${answerValue}」は無効なため除外しました。`,
      );
      return false;
    });
    if (validValues.length > 0) {
      validAnswerEntries.push([
        questionId,
        { status: "answered", values: [...validValues].sort() },
      ]);
    }
  }

  const state: AtlasStateV1 = {
    stateVersion: 1,
    datasetVersion: catalogDatasetVersion,
    viewId: catalogViewId,
    viewVersion: catalogViewVersion,
    answers: Object.fromEntries(validAnswerEntries),
  };
  if (decoded.selectedNodeId !== undefined) {
    if (catalog.nodeIds.has(decoded.selectedNodeId)) {
      state.selectedNodeId = decoded.selectedNodeId;
    } else {
      warnings.push(
        `選択ノード「${decoded.selectedNodeId}」は現在のビューに存在しないため除外しました。`,
      );
    }
  }

  return { state, warnings };
}

export function toRecommendationAnswers(state: AtlasStateV1): Record<string, string[]> {
  const validated = validateStateShape(state);
  return Object.fromEntries(
    Object.entries(validated.answers)
      .filter(([, answer]) => answer.status !== "not_applicable")
      .map(([questionId, answer]) => [
        questionId,
        answer.status === "unknown" ? ["unknown"] : [...answer.values].sort(),
      ]),
  );
}
