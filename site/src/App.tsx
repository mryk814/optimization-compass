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
import { ComparisonPage as CompareLabPage } from "./features/compare/ComparisonPage";
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

import "./styles.css";

const primaryNavigation = [
  { label: "Atlas", to: "/", matchPaths: ["/"] },
  { label: "Map", to: "/map", matchPaths: ["/map"] },
  { label: "診断", to: "/diagnose", matchPaths: ["/diagnose"] },
  { label: "手法", to: "/learn", matchPaths: ["/learn", "/methods"] },
  { label: "Gallery", to: "/gallery", matchPaths: ["/gallery"] },
  { label: "根拠", to: "/sources", matchPaths: ["/sources"] },
] as const;

function HomePage() {
  const links = useEntityLinks();
  const theater = links.status === "ready"
    ? links.index.entities.find((entity) => entity.entity_type === "trace" && entity.aliases.some((alias) => alias.startsWith("/theater/")))
    : undefined;
  const comparison = links.status === "ready"
    ? links.index.entities.find((entity) => entity.entity_type === "comparison")
    : undefined;
  return (
    <section className="home-page">
      <header className="home-hero">
        <p className="eyebrow">Optimization Compass</p>
        <h1>Optimization Atlas</h1>
        <p>問題の構造を整理し、手法を選び、動きと根拠まで一つの地図から確かめます。</p>
      </header>
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
        <article className="home-entry-card">
          <p className="home-entry-eyebrow">Watch & Compare</p>
          <h2>Method Theater</h2>
          <p>アルゴリズムの一手を再生し、同じ予算で動きを比べる。</p>
          <div className="home-entry-links">
            <Link to={theater?.canonical_url ?? "/learn"}>Theaterを開く</Link>
            <Link to={comparison?.canonical_url ?? "/learn"}>Compare Labを開く</Link>
          </div>
        </article>
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
    <article className="home-entry-card">
      <p className="home-entry-eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      <p>{description}</p>
      <Link to={to}>{linkLabel}</Link>
    </article>
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
  const comparisonRoute = links.status === "ready"
    ? links.index.entities.find((entity) => entity.entity_type === "comparison")?.canonical_url
    : undefined;
  const navigation = [
    ...primaryNavigation.slice(0, 4),
    { label: "比較", to: comparisonRoute ?? "/learn", matchPaths: ["/compare", "/theater", "/traces"] },
    ...primaryNavigation.slice(4),
  ];
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
          {navigation.map(({ label, to, matchPaths }) => {
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
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/diagnose" element={<DiagnosePage />} />
          <Route path="/methods/:methodId" element={<MethodPage />} />
          <Route path="/traces/:traceId" element={<TraceDemoPage />} />
          <Route path="/theater/search-tree/:artifactId" element={<SearchTreeTheaterPage />} />
          <Route path="/theater/bayesian-optimization" element={<BayesianOptimizationPage />} />
          <Route path="/compare/:comparisonId" element={<CanonicalRoute><CompareLabPage /></CanonicalRoute>} />
          <Route path="/gallery" element={<GalleryPage />} />
          <Route path="/gallery/:caseId" element={<GalleryCasePage />} />
          <Route path="/sources" element={<SourceIndexPage />} />
          <Route path="/sources/:sourceId" element={<SourceDetailPage />} />
          <Route path="/coverage" element={<CoveragePage />} />
          <Route path="/learn" element={<ContentIndexPage />} />
          <Route path="/learn/:contentId" element={<CanonicalRoute><ContentPage /></CanonicalRoute>} />
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
