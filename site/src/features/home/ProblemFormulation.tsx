import type { ProblemDefinition, ProblemInstance } from "../../contracts/problems";

interface ProblemFormulationProps {
  constraintsSummary: string;
  decisionVariablesSummary: string;
  definition: ProblemDefinition;
  instance: ProblemInstance;
  objectiveSummary: string;
}

export interface ReadableProblemFormulation {
  ariaLabel: string;
  constraints: string[];
  objective: string;
  sense: "minimize" | "maximize" | "objectives";
  variables: string;
}

export function ProblemFormulation({
  constraintsSummary,
  decisionVariablesSummary,
  definition,
  instance,
  objectiveSummary,
}: ProblemFormulationProps) {
  const formulation = buildReadableProblemFormulation(definition, instance);

  return (
    <section aria-labelledby="home-formulation-title" className="home-mathematical-formulation">
      <header>
        <p className="eyebrow">Mathematical formulation</p>
        <h3 id="home-formulation-title">このケースを定式化すると</h3>
      </header>
      <div aria-label={formulation.ariaLabel} className="home-formula" role="group">
        <div className="home-formula-line">
          <span>variables</span>
          <code>{formulation.variables}</code>
        </div>
        <div className="home-formula-line">
          <span>{formulation.sense}</span>
          <code>{formulation.objective}</code>
        </div>
        <div className="home-formula-line home-formula-constraints">
          <span>subject to</span>
          <div>
            {formulation.constraints.map((constraint) => (
              <code key={constraint}>{constraint}</code>
            ))}
          </div>
        </div>
      </div>
      <p className="home-formulation-reading">
        <strong>読み下し</strong>
        <span>選ぶもの: {decisionVariablesSummary}</span>
        <span>目的: {objectiveSummary}</span>
        <span>制約: {constraintsSummary}</span>
      </p>
    </section>
  );
}

export function buildReadableProblemFormulation(
  definition: ProblemDefinition,
  instance: ProblemInstance,
): ReadableProblemFormulation {
  const symbols = variableSymbols(instance);
  const variables = `(${symbols.join(", ")}) ∈ ${domain(definition.variable_domain, instance.dimension)}`;
  const sense = objectiveSense(definition.objective_direction);
  const objective = objectiveExpression(instance, symbols, definition.objective_direction);
  const constraints = [
    ...constraintExpressions(instance),
    ...boundExpressions(instance, symbols),
  ];
  const visibleConstraints = constraints.length > 0 ? constraints : ["制約なし"];

  return {
    ariaLabel: `${variables}; ${sense} ${objective}; subject to ${visibleConstraints.join("; ")}`,
    constraints: visibleConstraints,
    objective,
    sense,
    variables,
  };
}

function variableSymbols(instance: ProblemInstance): string[] {
  const boundKeys = Object.keys(instance.bounds).slice(0, instance.dimension);
  if (boundKeys.length === instance.dimension && boundKeys.every(isReadableSymbol)) {
    return boundKeys;
  }

  const axisLabels = instance.display.axis_labels;
  if (
    Array.isArray(axisLabels)
    && axisLabels.slice(0, instance.dimension).every((label) => (
      typeof label === "string" && isReadableSymbol(label)
    ))
  ) {
    return axisLabels.slice(0, instance.dimension) as string[];
  }
  return Array.from({ length: instance.dimension }, (_, index) => `x${subscript(index + 1)}`);
}

function isReadableSymbol(value: string): boolean {
  return /^[\p{L}_][\p{L}\p{N}_₀-₉]*$/u.test(value);
}

function domain(variableDomain: string, dimension: number): string {
  const exponent = superscript(dimension);
  if (variableDomain === "continuous") return `ℝ${exponent}`;
  if (variableDomain === "integer") return `ℤ${exponent}`;
  if (variableDomain === "binary") return `{0, 1}${exponent}`;
  if (variableDomain === "permutation") return `S${subscript(dimension)}`;
  return `${variableDomain}${exponent}`;
}

function objectiveSense(
  direction: ProblemDefinition["objective_direction"],
): ReadableProblemFormulation["sense"] {
  if (direction === "maximize") return "maximize";
  if (direction === "multiobjective") return "objectives";
  return "minimize";
}

function objectiveExpression(
  instance: ProblemInstance,
  symbols: string[],
  direction: ProblemDefinition["objective_direction"],
): string {
  const displayExpression = instance.display.expression;
  if (typeof displayExpression !== "string" || !displayExpression.trim()) {
    return `f(${symbols.join(", ")})`;
  }
  const normalized = normalizeExpression(displayExpression);
  if (direction === "multiobjective") return normalized;
  const objectivePart = normalized.split(/\s+s\.t\.\s+/iu, 1)[0]
    .replace(/^(?:min(?:imize)?|max(?:imize)?)\s+/iu, "")
    .trim();
  return objectivePart.includes("=")
    ? objectivePart
    : `f(${symbols.join(", ")}) = ${objectivePart}`;
}

function constraintExpressions(instance: ProblemInstance): string[] {
  return instance.constraints.flatMap((constraint) => {
    const expression = constraint.expression;
    return typeof expression === "string" && expression.trim()
      ? [normalizeExpression(expression)]
      : [];
  });
}

function boundExpressions(instance: ProblemInstance, symbols: string[]): string[] {
  const boundKeys = Object.keys(instance.bounds);
  return symbols.flatMap((symbol, index) => {
    const key = Object.hasOwn(instance.bounds, symbol) ? symbol : boundKeys[index];
    const value = key ? instance.bounds[key] : undefined;
    if (
      !Array.isArray(value)
      || value.length !== 2
      || value.some((entry) => typeof entry !== "number")
    ) {
      return [];
    }
    const [lower, upper] = value as [number, number];
    return [`${formatNumber(lower)} ≤ ${symbol} ≤ ${formatNumber(upper)}`];
  });
}

function normalizeExpression(value: string): string {
  return value
    .replaceAll("<=", "≤")
    .replaceAll(">=", "≥")
    .replaceAll("^2", "²")
    .replaceAll("-", "−")
    .replace(/\s+/gu, " ")
    .trim();
}

function formatNumber(value: number): string {
  return String(value).replace("-", "−");
}

function superscript(value: number): string {
  const digits: Record<string, string> = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
  };
  return String(value).split("").map((digit) => digits[digit] ?? digit).join("");
}

function subscript(value: number): string {
  const digits: Record<string, string> = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
  };
  return String(value).split("").map((digit) => digits[digit] ?? digit).join("");
}
