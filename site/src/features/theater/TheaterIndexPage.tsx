import { Link } from "react-router-dom";

import { THEATER_ROUTES } from "./theater-routes";

const theaterEntries = [
  {
    eyebrow: "Simplex geometry · AlgorithmTrace",
    title: "Nelder–Mead",
    description: "simplexの反射・拡張・収縮を、目的関数上の幾何操作として追います。",
    detail: "Nelder–Meadの幾何操作",
    to: THEATER_ROUTES.nelderMead,
  },
  {
    eyebrow: "Search tree · executable trace",
    title: "Branch-and-bound",
    description: "0-1 knapsackで、探索ノードの展開と最適性証明までを再生します。",
    detail: "Search-tree Theater",
    to: THEATER_ROUTES.searchTree,
  },
  {
    eyebrow: "Surrogate uncertainty · executable trace",
    title: "Bayesian Optimization（BO）",
    description: "観測からsurrogateを更新し、Expected Improvementで次の点を選ぶ流れを見ます。",
    detail: "BO Theater",
    to: THEATER_ROUTES.bayesianOptimization,
  },
] as const;

export function TheaterIndexPage() {
  return (
    <section className="atlas-page theater-index-page">
      <header className="atlas-page-header">
        <p className="eyebrow">Method Theater · Watch the mechanism</p>
        <h1>Method Theater</h1>
        <p>手法ごとの動きを選んで再生します。個別の実験に入る前に、何を観察するかを選べます。</p>
      </header>
      <div className="theater-card-grid" aria-label="Theaterの再生メニュー">
        {theaterEntries.map((entry) => (
          <Link className="theater-card" key={entry.to} to={entry.to}>
            <span>{entry.eyebrow}</span>
            <h2>{entry.title}</h2>
            <p>{entry.description}</p>
            <small>{entry.detail}を開く →</small>
          </Link>
        ))}
      </div>
    </section>
  );
}
