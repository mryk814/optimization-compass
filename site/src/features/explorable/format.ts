const MINUS = "−";

/** Fixed-digit number with a true minus sign; very large or tiny values switch to exponents. */
export function fmt(value: number, digits = 2): string {
  if (!Number.isFinite(value)) return value > 0 ? "∞" : value < 0 ? `${MINUS}∞` : "—";
  const magnitude = Math.abs(value);
  const text = magnitude !== 0 && (magnitude >= 1e5 || magnitude < 10 ** -digits)
    ? magnitude.toExponential(1).replace("e+", "e")
    : magnitude.toFixed(digits);
  const negative = value < 0 && Number(text) !== 0;
  return `${negative ? MINUS : ""}${text}`;
}

/** Plain-text alternative for a coordinate pair. */
export function fmtPair(x: number, y: number, digits = 2): string {
  return `(${fmt(x, digits)}, ${fmt(y, digits)})`;
}
