import type { MouseEvent } from "react";
import {
  HashRouter,
  Link,
  Route,
  Routes,
  useLocation,
  useParams,
} from "react-router-dom";

import "./styles.css";

const primaryNavigation = [
  { label: "Atlas", to: "/", matchPrefix: "/" },
  { label: "Map", to: "/map", matchPrefix: "/map" },
  { label: "診断", to: "/diagnose", matchPrefix: "/diagnose" },
  { label: "手法", to: "/methods/overview", matchPrefix: "/methods/" },
  { label: "比較", to: "/compare/overview", matchPrefix: "/compare/" },
  { label: "Gallery", to: "/gallery", matchPrefix: "/gallery" },
] as const;

type PurposePageProps = {
  heading: string;
  purpose: string;
};

function PurposePage({ heading, purpose }: PurposePageProps) {
  return (
    <section className="page-panel">
      <h1>{heading}</h1>
      <p>{purpose}</p>
      <p className="placeholder-note">この画面の機能は、次の実装スライスで追加します。</p>
    </section>
  );
}

function HomePage() {
  return (
    <section className="page-panel">
      <p className="eyebrow">Optimization Compass</p>
      <h1>Optimization Atlas</h1>
      <p>
        問題構造からたどる地図、条件を整理する診断、手法の理解、比較、実問題の事例を一つの入口から探します。
      </p>
    </section>
  );
}

function MethodPage() {
  const { methodId } = useParams();

  return (
    <section className="page-panel">
      <h1>手法を理解する</h1>
      <p>最適化手法の前提、直感、適用範囲を確認する画面です。</p>
      <p className="route-parameter">
        Method ID: <strong>{methodId}</strong>
      </p>
    </section>
  );
}

function ComparisonPage() {
  const { comparisonId } = useParams();

  return (
    <section className="page-panel">
      <h1>手法を比較する</h1>
      <p>同じ評価予算と条件で、複数の手法の動きを比較する画面です。</p>
      <p className="route-parameter">
        Comparison ID: <strong>{comparisonId}</strong>
      </p>
    </section>
  );
}

function CasePage() {
  const { caseId } = useParams();

  return (
    <section className="page-panel">
      <h1>ケース詳細</h1>
      <p>実問題の目的、制約、選択した手法、得られた知見を確認する画面です。</p>
      <p className="route-parameter">
        Case ID: <strong>{caseId}</strong>
      </p>
    </section>
  );
}

function NotFoundPage() {
  return (
    <section className="page-panel">
      <h1>ページが見つかりません</h1>
      <p>指定されたアトラスの経路は存在しません。</p>
      <Link className="text-link" to="/">
        Atlasへ戻る
      </Link>
    </section>
  );
}

function AppShell() {
  const { pathname } = useLocation();
  const skipToMain = (event: MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    document.getElementById("main-content")?.focus();
  };

  return (
    <div className="site-shell">
      <a className="skip-link" href="#main-content" onClick={skipToMain}>
        本文へ移動
      </a>
      <header className="site-header">
        <Link className="brand" to="/" aria-label="Optimization Atlas ホーム">
          <span aria-hidden="true" className="brand-mark">
            OC
          </span>
          <span>Optimization Atlas</span>
        </Link>
        <nav className="primary-navigation" aria-label="主要ナビゲーション">
          {primaryNavigation.map(({ label, to, matchPrefix }) => {
            const isActive =
              matchPrefix === "/" ? pathname === "/" : pathname.startsWith(matchPrefix);

            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "nav-link nav-link-active" : "nav-link"}
                key={to}
                to={to}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route
            path="/map"
            element={
              <PurposePage
                heading="問題構造マップ"
                purpose="最適化問題の構造を分岐ごとにたどり、関連する手法へ進む画面です。"
              />
            }
          />
          <Route
            path="/diagnose"
            element={
              <PurposePage
                heading="診断"
                purpose="問題の条件を整理し、候補・除外・代替解法を確認する画面です。"
              />
            }
          />
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/compare/:comparisonId" element={<ComparisonPage />} />
          <Route
            path="/gallery"
            element={
              <PurposePage
                heading="ケースギャラリー"
                purpose="材料、設計、運用などの実問題から、考え方と手法を逆引きする画面です。"
              />
            }
          />
          <Route path="/gallery/:caseId" element={<CasePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <span>Dataset 0.2.0</span>
        <span aria-hidden="true">·</span>
        <span>ViewSpec 1.0.0</span>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <HashRouter>
      <AppShell />
    </HashRouter>
  );
}
