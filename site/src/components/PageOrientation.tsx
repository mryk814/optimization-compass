import { Link } from "react-router-dom";

export interface PageOrientationLink {
  label: string;
  to: string;
}

export interface PageOrientationProps {
  purpose: string;
  readingSteps: readonly string[];
  limits: string;
  next: readonly PageOrientationLink[];
}

export function PageOrientation({ purpose, readingSteps, limits, next }: PageOrientationProps) {
  return (
    <aside className="page-orientation-shell" aria-label="このページの使い方">
      <details className="page-orientation-disclosure">
        <summary>
          <span className="page-orientation-eyebrow">Page guide</span>
          <span className="page-orientation-summary-title">このページの見方</span>
          <span className="page-orientation-summary-hint">目的・読み方・限界・次の導線</span>
        </summary>
        <div className="page-orientation">
          <section className="page-orientation-purpose">
            <h2>このページで分かること</h2>
            <p>{purpose}</p>
          </section>
          <section>
            <h3>読み方</h3>
            <ol>
              {readingSteps.map((step) => <li key={step}>{step}</li>)}
            </ol>
          </section>
          <section>
            <h3>前提・限界</h3>
            <p>{limits}</p>
          </section>
          <nav aria-label="次に見る">
            <h3>次に見る</h3>
            <ul>
              {next.map((item) => <li key={item.to}><Link to={item.to}>{item.label} →</Link></li>)}
            </ul>
          </nav>
        </div>
      </details>
    </aside>
  );
}
