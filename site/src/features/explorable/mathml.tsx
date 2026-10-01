/**
 * Tiny MathML builder for equations whose numbers change while the reader plays with a figure.
 * Static formulas in articles are compiled to MathML on the server; these are the live counterpart.
 * Only identifiers, numbers, and operators generated in code reach the markup, and all are escaped.
 */

const escapeText = (text: string) => text
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;");

export const mi = (name: string) => `<mi>${escapeText(name)}</mi>`;
export const mn = (text: string) => `<mn>${escapeText(text)}</mn>`;
export const mo = (symbol: string) => `<mo>${escapeText(symbol)}</mo>`;
export const row = (...parts: string[]) => `<mrow>${parts.join("")}</mrow>`;
export const sub = (base: string, script: string) => `<msub>${base}${script}</msub>`;
export const sup = (base: string, script: string) => `<msup>${base}${script}</msup>`;
export const frac = (top: string, bottom: string) => `<mfrac>${top}${bottom}</mfrac>`;
export const paren = (...parts: string[]) => row(mo("("), ...parts, mo(")"));
/** A number that may be negative, with its sign split out so the layout stays aligned. */
export const signed = (text: string) => (
  text.startsWith("−") ? row(mo("−"), mn(text.slice(1))) : mn(text)
);
/** A term with explicit sign for use after another term: "+ 3" or "− 3". */
export const addend = (text: string) => (
  text.startsWith("−") ? row(mo("−"), mn(text.slice(1))) : row(mo("+"), mn(text))
);
export const tint = (kind: "teal" | "orange" | "red" | "navy", part: string) => (
  `<mstyle class="mx-${kind}">${part}</mstyle>`
);

interface LiveMathProps {
  /** Markup built with the helpers above. */
  markup: string;
  /** Plain-text reading for assistive technology. */
  label: string;
  block?: boolean;
}

export function LiveMath({ markup, label, block = false }: LiveMathProps) {
  return (
    <span
      aria-label={label}
      className={block ? "live-math live-math-block" : "live-math"}
      dangerouslySetInnerHTML={{
        __html: `<math display="${block ? "block" : "inline"}" aria-hidden="true">${markup}</math>`,
      }}
      role="math"
    />
  );
}
