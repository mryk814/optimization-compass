import {
  OPTIMIZATION_TERMS,
  VARIABLE_TYPE_DEFINITIONS,
} from "../content/optimization-language";

export function OptimizationProblemPrimer() {
  return (
    <section aria-labelledby="optimization-problem-primer-title" className="problem-primer">
      <header className="problem-primer-header">
        <p className="problem-primer-eyebrow">Formulation / 共通のものさし</p>
        <h2 id="optimization-problem-primer-title">まず、現実の問題をこの形に置きます</h2>
        <p>このAtlasでは、手法を選ぶ前に「何を決め、何を良くし、何を守るか」をそろえます。</p>
      </header>

      <div className="problem-primer-main">
        <div className="problem-primer-formula">
          <div
            aria-label="xがXに属する範囲でf(x)を最小化する"
            className="problem-primer-equation"
            role="img"
            dangerouslySetInnerHTML={{
              __html: '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mrow><munder><mo>minimize</mo><mrow><mi>x</mi><mo>∈</mo><mi>X</mi></mrow></munder><mspace width="0.8em"/><mi>f</mi><mo>(</mo><mi>x</mi><mo>)</mo></mrow></math>',
            }}
          />
          <p>
            <span>subject to</span>
            <span
              aria-label="g i (x)は0以下、h j (x)は0に等しい"
              className="problem-primer-constraint-equation"
              role="img"
              dangerouslySetInnerHTML={{
                __html: '<math xmlns="http://www.w3.org/1998/Math/MathML"><mrow><msub><mi>g</mi><mi>i</mi></msub><mo>(</mo><mi>x</mi><mo>)</mo><mo>≤</mo><mn>0</mn><mo>,</mo><mspace width="0.45em"/><msub><mi>h</mi><mi>j</mi></msub><mo>(</mo><mi>x</mi><mo>)</mo><mo>=</mo><mn>0</mn></mrow></math>',
              }}
            />
          </p>
          <small>最大化は、f(x)の符号を反転すると最小化として読めます。</small>
        </div>

        <div className="problem-primer-terms">
          {OPTIMIZATION_TERMS.map((term) => (
            <article key={term.symbol}>
              <code>{term.symbol}</code>
              <div><strong>{term.title}</strong><p>{term.description}</p></div>
            </article>
          ))}
        </div>
      </div>

      <div className="problem-primer-types">
        <p><strong>xの種類</strong><span>離散 (discrete) は飛び飛びの候補から選ぶ総称で、整数・0-1・カテゴリを含みます。</span></p>
        <ul>
          {VARIABLE_TYPE_DEFINITIONS.map((item) => (
            <li key={item.title}><strong>{item.title}</strong><span>{item.description}</span></li>
          ))}
        </ul>
      </div>
    </section>
  );
}
