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

/** Three significant digits, as the article prints them (43.9, 0.612, 0.0182, 0.00632). */
export function sig(value: number): string {
  if (value >= 100) return value.toFixed(0);
  if (value >= 10) return value.toFixed(1);
  if (value >= 1) return value.toFixed(2);
  return value.toPrecision(3);
}

/** α as plain text such as 1e-3 or 7.25e-4. */
export function alphaText(alpha: number): string {
  const [mantissa, exponent] = alpha.toExponential(2).split("e");
  const trimmed = mantissa.replace(/\.?0+$/, "");
  return `${trimmed}e${Number(exponent).toString().replace("-", MINUS)}`;
}
