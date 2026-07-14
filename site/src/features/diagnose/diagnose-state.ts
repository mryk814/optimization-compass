import type { AnswerType } from "../../contracts/site-data";
import type { AtlasStateV1 } from "../../state/atlas-state";

type AnswerAction = "set" | "toggle" | "not_applicable" | "clear";

export function updateDiagnosticAnswer(
  state: AtlasStateV1,
  questionId: string,
  answerType: AnswerType,
  action: AnswerAction,
  value?: string,
): AtlasStateV1 {
  const answers = structuredClone(state.answers);
  if (action === "clear") {
    delete answers[questionId];
  } else if (action === "not_applicable") {
    answers[questionId] = { status: "not_applicable", values: [] };
  } else if (value === "unknown") {
    answers[questionId] = { status: "unknown", values: ["unknown"] };
  } else if (value !== undefined && (answerType === "single_choice" || action === "set")) {
    answers[questionId] = { status: "answered", values: [value] };
  } else if (value !== undefined) {
    const current = answers[questionId];
    const values = current?.status === "answered" ? [...current.values] : [];
    const index = values.indexOf(value);
    if (index >= 0) values.splice(index, 1);
    else values.push(value);
    if (values.length === 0) delete answers[questionId];
    else answers[questionId] = { status: "answered", values };
  }
  return { ...state, answers };
}
