import { useEffect, useState, type MouseEvent } from "react";
import {
  HashRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import type { ReactNode } from "react";

import { MapPage } from "./features/map/MapPage";
import { DiagnosePage } from "./features/diagnose/DiagnosePage";
import { MethodPage } from "./features/methods/MethodPage";
import { TraceDemoPage } from "./features/playback/TraceDemoPage";
import { SearchTreeTheaterPage } from "./features/search-tree/SearchTreeTheaterPage";
import { BayesianOptimizationPage } from "./features/theater/BayesianOptimizationPage";
import { TheaterIndexPage } from "./features/theater/TheaterIndexPage";
import { ComparisonPage as CompareLabPage } from "./features/compare/ComparisonPage";
import { CompareLabIndexPage } from "./features/compare/CompareLabIndexPage";
import { COMPARE_LAB_ROUTE } from "./features/compare/compare-routes";
import { THEATER_ROUTES } from "./features/theater/theater-routes";
import { ContentIndexPage, ContentPage } from "./features/content/ContentPages";
import { GalleryCasePage, GalleryPage } from "./features/gallery/GalleryPage";
import { LicenseLinks } from "./features/licensing/LicenseLinks";
import { SourceDetailPage, SourceIndexPage } from "./features/evidence/SourcePages";
import { CoveragePage } from "./features/coverage/CoveragePage";
import { NotFoundPage } from "./features/navigation/NotFoundPage";
import { loadDatasetReleaseIdentity } from "./contracts/release";
import { resolveAlias } from "./contracts/entity-links";
import type { EntityLinkIndex } from "./contracts/entity-links";
import { EntityLinkProvider, useEntityLinks } from "./state/entity-links";
import { PageOrientation } from "./components/PageOrientation";
import { SafeBackButton } from "./components/SafeBackButton";
import { SearchPage } from "./features/search/SearchPage";
import { LearningSlicePage } from "./features/learning-slices/LearningSlicePage";

import "./styles.css";

const primaryNavigation = [
  { label: "ホーム", to: "/", matchPaths: ["/"] },
  { label: "地図", to: "/map", matchPaths: ["/map"] },
  { label: "診断", to: "/diagnose", matchPaths: ["/diagnose"] },
  { label: "手法", to: "/learn", matchPaths: ["/learn", "/methods"] },
  { label: "再生", to: THEATER_ROUTES.index, matchPaths: ["/theater", "/traces"] },
  { label: "比較", to: COMPARE_LAB_ROUTE, matchPaths: ["/compare"] },
  { label: "検索", to: "/search", matchPaths: ["/search"] },
  { label: "事例", to: "/gallery", matchPaths: ["/gallery"] },
  { label: "根拠", to: "/sources", matchPaths: ["/sources"] },
] as const;

function HomePage() {
  return (
    <section className="home-page">
      <header className="home-hero">
        <p className="eyebrow">Optimization Compass</p>
        <h1>Optimization Atlas</h1>
        <p>問題の構造を整理し、手法を選び、動きと根拠まで一つの地図から確かめます。</p>
      </header>
      <PageOrientation
        limits="Atlasは構造化データと固定された教材・可視化をつなぐ入口です。個別の実験結果や最終判断そのものではありません。"
        next={[
          { label: "問題構造をたどる", to: "/map" },
          { label: "条件から診断する", to: "/diagnose" },
          { label: "教材を読む", to: "/learn" },
        ]}
        purpose="問題を分類し、候補手法・教材・実行Trace・根拠へ迷わず進むための入口です。"
        readingSteps={[
          "まず目的に近い入口（Explore / Decide / Learn / Apply）を選びます。",
          "条件が整理できていなければDiagnose、構造から考えたければMapを開きます。",
          "動きや根拠を確認するときはTheater・Compare・Sourcesへ進みます。",
        ]}
      />
      <div className="home-entry-grid" aria-label="Atlasの主要な入口">
        <HomeEntry
          eyebrow="Explore"
          title="Map"
          description="問題構造と候補手法のつながりを地図でたどる。"
          to="/map"
          linkLabel="地図を見る"
        />
        <HomeEntry
          eyebrow="Decide"
          title="Diagnose"
          description="条件を順に答え、候補・除外・確認事項を整理する。"
          to="/diagnose"
          linkLabel="診断を始める"
        />
        <HomeEntry
          eyebrow="Learn"
          title="Methods"
          description="手法と概念を、直感・前提・コード・根拠から学ぶ。"
          to="/learn"
          linkLabel="教材を探す"
        />
        <HomeEntry
          eyebrow="Watch"
          title="Method Theater"
          description="一つの手法の内部で、次の一手がどう決まるかを再生する。"
          to={THEATER_ROUTES.index}
          linkLabel="動きを見る"
        />
        <HomeEntry
          eyebrow="Compare"
          title="Compare Lab"
          description="同じ問題・初期条件・予算で、複数手法の違いを横に並べる。"
          to={COMPARE_LAB_ROUTE}
          linkLabel="違いを比べる"
        />
        <HomeEntry
          eyebrow="Apply"
          title="Problem Gallery"
          description="実問題の目的・制約から診断と候補手法へ逆引きする。"
          to="/gallery"
          linkLabel="ケースを見る"
        />
      </div>
      <p className="home-maintainer-link"><Link to="/coverage">Atlas coverageと教材バックログを見る</Link></p>
    </section>
  );
}

function HomeEntry({
  eyebrow,
  title,
  description,
  to,
  linkLabel,
}: {
  eyebrow: string;
  title: string;
  description: string;
  to: string;
  linkLabel: string;
}) {
  return (
    <Link aria-label={`${title} — ${linkLabel}`} className="home-entry-link" to={to}>
      <article className="home-entry-card">
        <p className="home-entry-eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p>{description}</p>
        <span className="home-entry-action">{linkLabel} →</span>
      </article>
    </Link>
  );
}

function AppShell() {
  const { pathname } = useLocation();
  const [datasetVersion, setDatasetVersion] = useState<string>();
  useEffect(() => {
    const controller = new AbortController();
    void loadDatasetReleaseIdentity(controller.signal).then(
      (identity) => setDatasetVersion(identity.dataset_version),
      (error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setDatasetVersion(undefined);
        }
      },
    );
    return () => controller.abort();
  }, []);
  const links = useEntityLinks();
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
          {primaryNavigation.map(({ label, to, matchPaths }) => {
            const isActive = matchPaths.some((matchPath) =>
              matchPath === "/"
                ? pathname === matchPath
                : pathname === matchPath || pathname.startsWith(`${matchPath}/`),
            );

            return (
              <Link
                aria-current={isActive ? "page" : undefined}
                className={isActive ? "nav-link nav-link-active" : "nav-link"}
                key={label}
                to={to}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main id="main-content" tabIndex={-1}>
        <SafeBackButton />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/diagnose" element={<DiagnosePage />} />
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/traces/:traceId" element={<TraceDemoPage />} />
          <Route path={THEATER_ROUTES.index} element={<TheaterIndexPage />} />
          <Route path="/theater/search-tree/:artifactId" element={<SearchTreeTheaterPage />} />
          <Route path="/theater/bayesian-optimization" element={<BayesianOptimizationPage />} />
          <Route path="/theater/learning/:scenarioId" element={<LearningSlicePage />} />
          <Route path={COMPARE_LAB_ROUTE} element={<CompareLabIndexPage />} />
          <Route path="/compare/:comparisonId" element={<CanonicalRoute><CompareLabPage /></CanonicalRoute>} />
          <Route path="/gallery" element={<GalleryPage />} />
          <Route path="/gallery/:caseId" element={<GalleryCasePage />} />
          <Route path="/sources" element={<SourceIndexPage />} />
          <Route path="/sources/:sourceId" element={<SourceDetailPage />} />
          <Route path="/coverage" element={<CoveragePage />} />
          <Route path="/learn" element={<ContentIndexPage />} />
          <Route path="/learn/:contentId" element={<CanonicalRoute><ContentPage /></CanonicalRoute>} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/theater/:alias" element={<AliasRoute />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <span aria-live="polite">Dataset {datasetVersion ?? "…"}</span>
        <span aria-hidden="true">·</span>
        <span>ViewSpec 1.0.0</span>
        <span aria-hidden="true">·</span>
        <LicenseLinks />
        <span aria-hidden="true">·</span>
        <Link to="/coverage">Coverage</Link>
      </footer>
    </div>
  );
}

export default function App({ initialEntityLinks }: { initialEntityLinks?: EntityLinkIndex } = {}) {
  return (
    <HashRouter>
      <EntityLinkProvider initialIndex={initialEntityLinks}>
        <AppShell />
      </EntityLinkProvider>
    </HashRouter>
  );
}

function CanonicalRoute({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const links = useEntityLinks();
  if (links.status === "loading") return <p role="status">正規URLを確認しています…</p>;
  const target = links.status === "ready" ? resolveAlias(links.index, pathname) : undefined;
  return target?.canonical_url ? <Navigate replace to={target.canonical_url} /> : children;
}

function AliasRoute() {
  const { pathname } = useLocation();
  const links = useEntityLinks();
  if (links.status === "loading") return <p role="status">正規URLを確認しています…</p>;
  if (links.status === "error") return <NotFoundPage detail={links.error.message} />;
  const target = resolveAlias(links.index, pathname);
  return target?.canonical_url
    ? <Navigate replace to={target.canonical_url} />
    : <NotFoundPage detail={`登録されていないaliasです: ${pathname}`} />;
}
