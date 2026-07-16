import { useEffect, useRef, useState, type MouseEvent } from "react";
import {
  HashRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import type { ReactNode } from "react";

import { SafeBackButton } from "./components/SafeBackButton";
import { findEntity, resolveAlias, type EntityLinkIndex } from "./contracts/entity-links";
import { parseGalleryIndex } from "./contracts/gallery";
import { parseLearningJourneyIndex } from "./contracts/learning-journeys";
import { loadDatasetReleaseIdentity } from "./contracts/release";
import { siteBaseUrl } from "./data/base-url";
import { CompareLabIndexPage } from "./features/compare/CompareLabIndexPage";
import { ComparisonPage as CompareLabPage } from "./features/compare/ComparisonPage";
import { COMPARE_LAB_ROUTE } from "./features/compare/compare-routes";
import { ContentIndexPage, ContentPage } from "./features/content/ContentPages";
import { CoveragePage } from "./features/coverage/CoveragePage";
import { DiagnosePage } from "./features/diagnose/DiagnosePage";
import { SourceDetailPage, SourceIndexPage } from "./features/evidence/SourcePages";
import { GalleryCasePage, GalleryPage } from "./features/gallery/GalleryPage";
import { selectFeaturedCase, type FeaturedCase } from "./features/home/featured-case";
import { LearningSlicePage } from "./features/learning-slices/LearningSlicePage";
import { LicenseLinks } from "./features/licensing/LicenseLinks";
import { MapPage } from "./features/map/MapPage";
import { MethodPage } from "./features/methods/MethodPage";
import { NotFoundPage } from "./features/navigation/NotFoundPage";
import { TraceDemoPage } from "./features/playback/TraceDemoPage";
import { SearchPage } from "./features/search/SearchPage";
import { SearchTreeTheaterPage } from "./features/search-tree/SearchTreeTheaterPage";
import { BayesianOptimizationPage } from "./features/theater/BayesianOptimizationPage";
import { TheaterIndexPage } from "./features/theater/TheaterIndexPage";
import { THEATER_ROUTES } from "./features/theater/theater-routes";
import { EntityLinkProvider, useEntityLinks } from "./state/entity-links";
import { JourneyNavigation } from "./state/journey-navigation";

import "./styles.css";
import "./home.css";

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

const secondaryHomeLinks = [
  { label: "問題構造Map", to: "/map" },
  { label: "手法・概念を学ぶ", to: "/learn" },
  { label: "動きを見る", to: THEATER_ROUTES.index },
  { label: "条件を揃えて比べる", to: COMPARE_LAB_ROUTE },
  { label: "横断検索", to: "/search" },
  { label: "根拠を確認", to: "/sources" },
] as const;

function HomePage() {
  const links = useEntityLinks();
  const [featuredCase, setFeaturedCase] = useState<FeaturedCase | null>();

  useEffect(() => {
    const controller = new AbortController();
    void loadFeaturedCase(controller.signal).then(
      (item) => setFeaturedCase(item),
      (error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setFeaturedCase(null);
        }
      },
    );
    return () => controller.abort();
  }, []);

  const methodLabel = (methodId: string) => (
    links.status === "ready"
      ? findEntity(links.index, "method", methodId)?.label ?? methodId
      : methodId
  );
  const candidate = featuredCase?.item.candidate_methods[0];
  const excluded = featuredCase?.item.excluded_methods[0];

  return (
    <section className="home-page">
      <header className="home-hero">
        <p className="eyebrow">Optimization Compass</p>
        <h1>最適化したい。でも、何をどう解けばいい？</h1>
        <p>
          現実の問いを定式化し、候補だけでなく除外理由・失敗の兆候・根拠まで辿るAtlasです。
        </p>
        <div className="home-primary-actions" aria-label="最初の選択">
          <Link className="home-primary-action" to="/diagnose">条件から診断する</Link>
          <Link className="home-secondary-action" to="/gallery">実例から探す</Link>
        </div>
      </header>

      <section aria-labelledby="home-case-title" className="home-case-preview" aria-live="polite">
        {featuredCase === undefined && (
          <div className="home-case-loading" role="status">
            <p className="eyebrow">Case preview</p>
            <h2 id="home-case-title">実問題を読み込んでいます</h2>
          </div>
        )}
        {featuredCase === null && (
          <div className="home-case-loading">
            <p className="eyebrow">Problem first</p>
            <h2 id="home-case-title">問いを、変数・目的・制約へ分解する</h2>
            <p>Galleryでは、Caseごとに候補・条件付き候補・除外理由を同じ形式で確認できます。</p>
            <Link className="text-link" to="/gallery">Case一覧を開く →</Link>
          </div>
        )}
        {featuredCase && (
          <>
            <header className="home-case-header">
              <div>
                <p className="eyebrow">Case preview · {featuredCase.item.domain}</p>
                <h2 id="home-case-title">{featuredCase.item.title_ja}</h2>
                <p className="home-case-question">{featuredCase.item.question}</p>
              </div>
              <Link className="home-case-link" to={featuredCase.canonicalUrl}>
                このCaseを辿る →
              </Link>
            </header>

            <dl className="home-case-formulation">
              <div><dt>変数</dt><dd>{featuredCase.item.decision_variables}</dd></div>
              <div><dt>目的</dt><dd>{featuredCase.item.objective}</dd></div>
              <div><dt>制約</dt><dd>{featuredCase.item.constraints}</dd></div>
            </dl>

            <div className="home-case-dispositions">
              <article className="home-disposition-candidate">
                <span>候補</span>
                <strong>{candidate ? methodLabel(candidate.method_id) : "Case内で確認"}</strong>
                <p>{candidate?.reason ?? "問題構造と利用可能な情報に合う主要候補です。"}</p>
              </article>
              <article className="home-disposition-excluded">
                <span>選ばない理由</span>
                <strong>{excluded ? methodLabel(excluded.method_id) : "前提違反を確認"}</strong>
                <p>{excluded?.reason ?? "候補だけでなく、適用を避ける条件も明示します。"}</p>
              </article>
            </div>
          </>
        )}
      </section>

      <nav aria-label="Atlasのその他の入口" className="home-secondary-nav">
        <p>必要になったら</p>
        <div>
          {secondaryHomeLinks.map((item) => (
            <Link key={item.to} to={item.to}>{item.label}</Link>
          ))}
        </div>
      </nav>

      <p className="home-scope-note">
        Theater・Compareは、接続済みの固定Caseと条件で提供します。一般的な手法順位を示すものではありません。
        <Link to="/coverage"> Coverageを見る</Link>
      </p>
    </section>
  );
}

async function loadFeaturedCase(signal: AbortSignal): Promise<FeaturedCase | null> {
  const base = siteBaseUrl();
  const [galleryResponse, journeyResponse] = await Promise.all([
    fetch(`${base}data/gallery.json`, { signal }),
    fetch(`${base}data/learning-journeys.json`, { signal }),
  ]);
  if (!galleryResponse.ok) {
    throw new Error(`Gallery request failed (${galleryResponse.status}).`);
  }
  if (!journeyResponse.ok) {
    throw new Error(`Learning journey request failed (${journeyResponse.status}).`);
  }
  return selectFeaturedCase(
    parseGalleryIndex(await galleryResponse.json()),
    parseLearningJourneyIndex(await journeyResponse.json()),
  );
}

function AppShell() {
  const { pathname } = useLocation();
  const previousPathname = useRef(pathname);
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
  useEffect(() => {
    if (previousPathname.current === pathname) return;
    previousPathname.current = pathname;
    document.getElementById("main-content")?.focus({ preventScroll: true });
  }, [pathname]);
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
        <JourneyNavigation />
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
  const { pathname, search } = useLocation();
  const links = useEntityLinks();
  if (links.status === "loading") return <p role="status">正規URLを確認しています…</p>;
  const target = links.status === "ready" ? resolveAlias(links.index, pathname) : undefined;
  return target?.canonical_url
    ? <Navigate replace to={{ pathname: target.canonical_url, search }} />
    : children;
}

function AliasRoute() {
  const { pathname, search } = useLocation();
  const links = useEntityLinks();
  if (links.status === "loading") return <p role="status">正規URLを確認しています…</p>;
  if (links.status === "error") return <NotFoundPage detail={links.error.message} />;
  const target = resolveAlias(links.index, pathname);
  return target?.canonical_url
    ? <Navigate replace to={{ pathname: target.canonical_url, search }} />
    : <NotFoundPage detail={`登録されていないaliasです: ${pathname}`} />;
}
