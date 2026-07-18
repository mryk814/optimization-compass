import type { ProblemDefinition, ProblemInstance } from "../../contracts/problems";

interface ProblemFormulationProps {
  constraintsSummary: string;
  decisionVariablesSummary: string;
  formulation: ReadableProblemFormulation;
  objectiveSummary: string;
}

export interface ReadableProblemFormulation {
  ariaLabel: string;
  constraints: string[];
  objective: string;
  sense: "minimize" | "maximize" | "objectives";
  variables: string;
}

interface VariableBounds {
  bounds: [number, number][];
  symbols: string[];
}

interface KnapsackItem {
  item_id: string;
  value: number;
  weight: number;
}

export function ProblemFormulation({
  constraintsSummary,
  decisionVariablesSummary,
  formulation,
  objectiveSummary,
}: ProblemFormulationProps) {
  return (
    <section aria-labelledby="home-formulation-title" className="home-mathematical-formulation">
      <header>
        <p className="eyebrow">Mathematical formulation</p>
        <h3 id="home-formulation-title">このケースを定式化すると</h3>
      </header>
      <div aria-label={formulation.ariaLabel} className="home-formula" role="group">
        <div className="home-formula-line">
          <span>variables / 変数</span>
          <code>{formulation.variables}</code>
        </div>
        <div className="home-formula-line">
          <span>{formulation.sense}</span>
          <code>{formulation.objective}</code>
        </div>
        <div className="home-formula-line home-formula-constraints">
          <span>subject to / 制約</span>
          <div>
            {formulation.constraints.map((constraint) => (
              <code key={constraint}>{constraint}</code>
            ))}
          </div>
        </div>
      </div>
      <p className="home-formulation-reading">
        <strong>式を言葉で読むと</strong>
        <span>決めるもの: {decisionVariablesSummary}</span>
        <span>良くしたいもの: {objectiveSummary}</span>
        <span>守る条件: {constraintsSummary}</span>
      </p>
    </section>
  );
}

export function buildReadableProblemFormulation(
  definition: ProblemDefinition,
  instance: ProblemInstance,
): ReadableProblemFormulation | null {
  if (!domain(definition.variable_domain, instance.dimension)) return null;

  const knapsack = buildKnapsackFormulation(definition, instance);
  if (knapsack) return knapsack;

  const variableBounds = parsePerVariableBounds(instance);
  if (!variableBounds) return null;
  const variablesDomain = domain(definition.variable_domain, instance.dimension);
  if (!variablesDomain) return null;
  const variables = `(${variableBounds.symbols.join(", ")}) ∈ ${variablesDomain}`;
  const sense = objectiveSense(definition.objective_direction);
  const objective = objectiveExpression(instance, variableBounds.symbols, definition.objective_direction);
  const constraints = constraintExpressions(instance);
  if (!objective || !constraints) return null;

  const bounds = variableBounds.symbols.map((symbol, index) => {
    const [lower, upper] = variableBounds.bounds[index];
    return `${formatNumber(lower)} ≤ ${symbol} ≤ ${formatNumber(upper)}`;
  });
  const visibleConstraints = [...constraints, ...bounds];
  if (visibleConstraints.length === 0) visibleConstraints.push("制約なし");

  return readableFormulation(variables, sense, objective, visibleConstraints);
}

function buildKnapsackFormulation(
  definition: ProblemDefinition,
  instance: ProblemInstance,
): ReadableProblemFormulation | null {
  if (
    definition.mathematical_family !== "binary_knapsack"
    || definition.variable_domain !== "binary"
    || definition.objective_direction !== "maximize"
  ) {
    return null;
  }

  const items = parseKnapsackItems(instance.parameters.items, instance.dimension);
  const rawBounds = instance.bounds.variables;
  const capacity = instance.parameters.capacity;
  if (
    !items
    || !Array.isArray(rawBounds)
    || rawBounds.length !== instance.dimension
    || !rawBounds.every(isBinaryBound)
    || typeof capacity !== "number"
    || !Number.isFinite(capacity)
    || instance.constraints.length !== 1
  ) {
    return null;
  }
  const constraint = instance.constraints[0];
  if (
    constraint.constraint_id !== "capacity"
    || constraint.sense !== "lte"
    || constraint.rhs !== capacity
  ) {
    return null;
  }

  const symbols = items.map((item) => item.item_id);
  const variables = `(${symbols.join(", ")}) ∈ ${domain("binary", instance.dimension)}`;
  const objective = `f(${symbols.join(", ")}) = ${linearExpression(items, "value")}`;
  const constraints = [
    `${linearExpression(items, "weight")} ≤ ${formatNumber(capacity)}`,
    ...symbols.map((symbol) => `0 ≤ ${symbol} ≤ 1`),
  ];
  return readableFormulation(variables, "maximize", objective, constraints);
}

function parseKnapsackItems(value: unknown, dimension: number): KnapsackItem[] | null {
  if (!Array.isArray(value) || value.length !== dimension) return null;
  const items = value.flatMap((entry) => {
    if (typeof entry !== "object" || entry === null || Array.isArray(entry)) return [];
    const item = entry as Record<string, unknown>;
    if (
      typeof item.item_id !== "string"
      || !isReadableSymbol(item.item_id)
      || typeof item.value !== "number"
      || !Number.isFinite(item.value)
      || typeof item.weight !== "number"
      || !Number.isFinite(item.weight)
    ) {
      return [];
    }
    return [{ item_id: item.item_id, value: item.value, weight: item.weight }];
  });
  if (items.length !== dimension || new Set(items.map((item) => item.item_id)).size !== dimension) {
    return null;
  }
  return items;
}

function isBinaryBound(value: unknown): boolean {
  return Array.isArray(value) && value.length === 2 && value[0] === 0 && value[1] === 1;
}

function linearExpression(items: KnapsackItem[], field: "value" | "weight"): string {
  return items.map((item) => `${formatNumber(item[field])}${item.item_id}`).join("+");
}

function parsePerVariableBounds(instance: ProblemInstance): VariableBounds | null {
  const entries = Object.entries(instance.bounds);
  if (entries.length !== instance.dimension) return null;
  const symbols: string[] = [];
  const bounds: [number, number][] = [];
  for (const [symbol, value] of entries) {
    if (!isReadableVariableSymbol(symbol) || !isNumericBound(value)) return null;
    symbols.push(symbol);
    bounds.push(value);
  }
  return { bounds, symbols };
}

function isNumericBound(value: unknown): value is [number, number] {
  return Array.isArray(value)
    && value.length === 2
    && value.every((entry) => typeof entry === "number" && Number.isFinite(entry));
}

function isReadableVariableSymbol(value: string): boolean {
  return !["assignment_columns", "lower", "parameter_names", "upper", "variables"].includes(value)
    && isReadableSymbol(value);
}

function isReadableSymbol(value: string): boolean {
  return /^[\p{L}_][\p{L}\p{N}_₀-₉]*$/u.test(value);
}

function domain(variableDomain: string, dimension: number): string | null {
  const exponent = superscript(dimension);
  if (variableDomain === "continuous") return `ℝ${exponent}`;
  if (variableDomain === "integer") return `ℤ${exponent}`;
  if (variableDomain === "binary") return `{0, 1}${exponent}`;
  if (variableDomain === "permutation") return `S${subscript(dimension)}`;
  return null;
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
): string | null {
  const displayExpression = instance.display.expression;
  if (typeof displayExpression !== "string" || !displayExpression.trim()) return null;
  const normalized = normalizeExpression(displayExpression);
  if (direction === "multiobjective") return normalized;
  if (normalized.includes(";")) return null;

  const explicitSense = normalized.match(/^(min(?:imize)?|max(?:imize)?)\s+/iu)?.[1]?.toLowerCase();
  if (
    (explicitSense?.startsWith("min") && direction !== "minimize")
    || (explicitSense?.startsWith("max") && direction !== "maximize")
  ) {
    return null;
  }
  const objectivePart = normalized.split(/\s+s\.t\.\s+/iu, 1)[0]
    .replace(/^(?:min(?:imize)?|max(?:imize)?)\s+/iu, "")
    .trim();
  if (!objectivePart) return null;
  return objectivePart.includes("=")
    ? objectivePart
    : `f(${symbols.join(", ")}) = ${objectivePart}`;
}

function constraintExpressions(instance: ProblemInstance): string[] | null {
  const expressions: string[] = [];
  for (const constraint of instance.constraints) {
    const expression = constraint.expression;
    if (typeof expression !== "string" || !expression.trim()) return null;
    expressions.push(normalizeExpression(expression));
  }
  return expressions;
}

function readableFormulation(
  variables: string,
  sense: ReadableProblemFormulation["sense"],
  objective: string,
  constraints: string[],
): ReadableProblemFormulation {
  return {
    ariaLabel: `${variables}; ${sense} ${objective}; subject to ${constraints.join("; ")}`,
    constraints,
    objective,
    sense,
    variables,
  };
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
