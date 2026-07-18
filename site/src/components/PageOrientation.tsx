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
          <span className="page-orientation-summary-title">このページでの読み方</span>
          <span className="page-orientation-summary-hint">目的・読む順番・前提・次に進む先</span>
        </summary>
        <div className="page-orientation">
          <section className="page-orientation-purpose">
            <h2>このページの目的</h2>
            <p>{purpose}</p>
          </section>
          <section>
            <h3>読む順番</h3>
            <ol>
              {readingSteps.map((step) => <li key={step}>{step}</li>)}
            </ol>
          </section>
          <section>
            <h3>前提・限界</h3>
            <p>{limits}</p>
          </section>
          <nav aria-label="次に進む">
            <h3>次に進む</h3>
            <ul>
              {next.map((item) => <li key={item.to}><Link to={item.to}>{item.label} →</Link></li>)}
            </ul>
          </nav>
        </div>
      </details>
    </aside>
  );
}
