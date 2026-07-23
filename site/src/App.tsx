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
import { parseProblemCatalog } from "./contracts/problems";
import { loadDatasetReleaseIdentity } from "./contracts/release";
import { siteBaseUrl } from "./data/base-url";
import { CompareLabIndexPage } from "./features/compare/CompareLabIndexPage";
import { ComparisonPage as CompareLabPage } from "./features/compare/ComparisonPage";
import { COMPARE_LAB_ROUTE } from "./features/compare/compare-routes";
import { ContentIndexPage, ContentPage } from "./features/content/ContentPages";
import { CoveragePage } from "./features/coverage/CoveragePage";
import { DataPage } from "./features/data/DataPage";
import { DiagnosePage } from "./features/diagnose/DiagnosePage";
import { SourceDetailPage, SourceIndexPage } from "./features/evidence/SourcePages";
import { FailureModePage } from "./features/failures/FailureModePage";
import { domainLabel, GalleryCasePage, GalleryPage } from "./features/gallery/GalleryPage";
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
  { label: "条件で診断", to: "/diagnose", matchPaths: ["/diagnose"] },
  { label: "事例を見る", to: "/gallery", matchPaths: ["/gallery"] },
  { label: "手法を学ぶ", to: "/learn", matchPaths: ["/learn", "/methods"] },
] as const;

const exploreNavigation = [
  { label: "動きを見る", to: THEATER_ROUTES.index, matchPaths: ["/theater", "/traces"] },
  { label: "条件を比較", to: COMPARE_LAB_ROUTE, matchPaths: ["/compare"] },
  { label: "問題構造", to: "/map", matchPaths: ["/map"] },
  { label: "横断検索", to: "/search", matchPaths: ["/search"] },
  { label: "根拠を見る", to: "/sources", matchPaths: ["/sources"] },
] as const;

const secondaryHomeLinks = [
  { label: "問題構造をたどる", to: "/map" },
  { label: "手法・概念を学ぶ", to: "/learn" },
  { label: "動きを見る", to: THEATER_ROUTES.index },
  { label: "比較条件を揃える", to: COMPARE_LAB_ROUTE },
  { label: "横断して検索", to: "/search" },
  { label: "根拠を確認する", to: "/sources" },
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
  const primaryScenario = featuredCase?.journey.scenarios.find(
    (scenario) => scenario.role === "primary",
  );
  const comparison = featuredCase?.journey.comparisons[0];

  return (
    <section className="home-page">
      <header className="home-hero">
        <p className="eyebrow">Optimization Compass</p>
        <h1>最適化したい問いを、問題の形にする</h1>
        <p>
          現実の問いを変数・目的・制約に整理し、候補・除外理由・失敗の兆候・根拠を確認できるAtlasです。
        </p>
        <div className="home-primary-actions" aria-label="最初に選ぶ入口">
          <Link className="home-primary-action" to="/diagnose">条件から診断を始める</Link>
          <Link className="home-secondary-action" to="/gallery">実例から探す</Link>
        </div>
      </header>

      <section aria-labelledby="home-case-title" className="home-case-preview" aria-live="polite">
        {featuredCase === undefined && (
          <div className="home-case-loading" role="status">
            <p className="eyebrow">Case preview</p>
            <h2 id="home-case-title">ケースを読み込んでいます</h2>
          </div>
        )}
        {featuredCase === null && (
          <div className="home-case-loading">
            <p className="eyebrow">Problem first</p>
            <h2 id="home-case-title">問いを、変数・目的・制約に分けて見る</h2>
            <p>ギャラリーでケースを選ぶと、候補・条件付き候補・除外理由を同じ形式で確認できます。</p>
            <Link className="text-link" to="/gallery">ギャラリーでケースを選ぶ →</Link>
          </div>
        )}
        {featuredCase && (
          <>
            <header className="home-case-header">
              <div>
                <p className="eyebrow">Case preview · {domainLabel(featuredCase.item.domain)}</p>
                <h2 id="home-case-title">{featuredCase.item.title_ja}</h2>
                <p className="home-case-question">{featuredCase.item.question}</p>
              </div>
              <Link className="home-case-link" to={featuredCase.canonicalUrl}>
                このCaseの詳細を見る →
              </Link>
            </header>

            <ol aria-label="このケースでたどる順番" className="home-case-journey">
              <li>
                <span>1</span>
                <div><strong>問いを選ぶ</strong><small>いま見ているCase</small></div>
              </li>
              <li>
                <span>2</span>
                <Link to={featuredCase.canonicalUrl}>
                  <strong>問題の形にする</strong><small>変数・目的・制約</small>
                </Link>
              </li>
              <li>
                <span>3</span>
                <Link to={primaryScenario?.canonical_url ?? THEATER_ROUTES.index}>
                  <strong>動きを見る</strong><small>固定した1回の実行</small>
                </Link>
              </li>
              <li>
                <span>4</span>
                <Link to={comparison?.canonical_url ?? COMPARE_LAB_ROUTE}>
                  <strong>条件を比べる</strong><small>固定したもの・変えたもの</small>
                </Link>
              </li>
            </ol>

            <details className="home-case-disclosure">
              <summary>候補と選ばない理由を見る</summary>
              <div className="home-case-dispositions">
                <article className="home-disposition-candidate">
                  <span>候補</span>
                  <strong>{candidate ? methodLabel(candidate.method_id) : "Case内で確認"}</strong>
                  <p>{candidate?.reason ?? "問題構造と利用可能な情報に合う候補です。"}</p>
                </article>
                <article className="home-disposition-excluded">
                  <span>選ばない理由</span>
                  <strong>{excluded ? methodLabel(excluded.method_id) : "前提違反を確認"}</strong>
                  <p>{excluded?.reason ?? "候補だけでなく、適用を避ける条件も明示します。"}</p>
                </article>
              </div>
            </details>
          </>
        )}
      </section>

      <nav aria-label="次に進む入口" className="home-secondary-nav">
        <p>目的に合わせて選ぶ</p>
        <div>
          {secondaryHomeLinks.map((item) => (
            <Link key={item.to} to={item.to}>{item.label}</Link>
          ))}
        </div>
      </nav>

      <p className="home-scope-note">
        Theater・Compareは、接続済みの固定Caseと条件で読みます。一般的な手法順位は示しません。
        <Link to="/coverage"> Coverageを確認</Link>
      </p>
    </section>
  );
}

async function loadFeaturedCase(signal: AbortSignal): Promise<FeaturedCase | null> {
  const base = siteBaseUrl();
  const [galleryResponse, journeyResponse, problemResponse] = await Promise.all([
    fetch(`${base}data/gallery.json`, { signal }),
    fetch(`${base}data/learning-journeys.json`, { signal }),
    fetch(`${base}data/problems.json`, { signal }),
  ]);
  if (!galleryResponse.ok) {
    throw new Error(`Gallery request failed (${galleryResponse.status}).`);
  }
  if (!journeyResponse.ok) {
    throw new Error(`Learning journey request failed (${journeyResponse.status}).`);
  }
  if (!problemResponse.ok) {
    throw new Error(`Problem catalog request failed (${problemResponse.status}).`);
  }
  return selectFeaturedCase(
    parseGalleryIndex(await galleryResponse.json()),
    parseLearningJourneyIndex(await journeyResponse.json()),
    parseProblemCatalog(await problemResponse.json()),
  );
}

function AppShell() {
  const { pathname } = useLocation();
  const previousPathname = useRef(pathname);
  const navigationOverflow = useRef<HTMLDetailsElement>(null);
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
    navigationOverflow.current?.removeAttribute("open");
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
        <Link className="brand" to="/" aria-label="Optimization Atlasのホーム">
          <span aria-hidden="true" className="brand-mark">
            OC
          </span>
          <span>Optimization Atlas</span>
        </Link>
        <nav className="primary-navigation" aria-label="主要ナビゲーション">
          {primaryNavigation.map(({ label, to, matchPaths }) => {
            const isActive = matchPaths.some((matchPath) =>
              pathname === matchPath || pathname.startsWith(`${matchPath}/`),
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
          <details className="navigation-overflow" ref={navigationOverflow}>
            <summary
              className={
                exploreNavigation.some(({ matchPaths }) => matchPaths.some((matchPath) =>
                  pathname === matchPath || pathname.startsWith(`${matchPath}/`),
                ))
                  ? "nav-link nav-link-active"
                  : "nav-link"
              }
            >
              探索
            </summary>
            <div>
              {exploreNavigation.map(({ label, to, matchPaths }) => {
                const isActive = matchPaths.some((matchPath) =>
                  pathname === matchPath || pathname.startsWith(`${matchPath}/`),
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
            </div>
          </details>
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
          <Route path="/theater/bayesian-optimization/:scenarioId" element={<BayesianOptimizationPage />} />
          <Route path="/theater/learning/:scenarioId" element={<LearningSlicePage />} />
          <Route path={COMPARE_LAB_ROUTE} element={<CompareLabIndexPage />} />
          <Route path="/compare/:comparisonId" element={<CanonicalRoute><CompareLabPage /></CanonicalRoute>} />
          <Route path="/gallery" element={<GalleryPage />} />
          <Route path="/gallery/:caseId" element={<GalleryCasePage />} />
          <Route path="/failures" element={<FailureModePage />} />
          <Route path="/sources" element={<SourceIndexPage />} />
          <Route path="/sources/:sourceId" element={<SourceDetailPage />} />
          <Route path="/coverage" element={<CoveragePage />} />
          <Route path="/data" element={<DataPage />} />
          <Route path="/learn" element={<ContentIndexPage />} />
          <Route path="/learn/:contentId" element={<CanonicalRoute><ContentPage /></CanonicalRoute>} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/theater/:alias" element={<AliasRoute />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <Link aria-live="polite" to="/data">Dataset {datasetVersion ?? "…"}</Link>
        <span aria-hidden="true">·</span>
        <span>ViewSpec 1.0.0</span>
        <span aria-hidden="true">·</span>
        <LicenseLinks />
        <span aria-hidden="true">·</span>
        <Link to="/coverage">Coverageを確認</Link>
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
