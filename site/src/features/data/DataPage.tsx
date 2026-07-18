import { useEffect, useState } from "react";

import { parseSiteManifest } from "../../contracts/manifest";
import {
  parseReleaseCatalog,
  type ReleaseCatalog,
  type ReleaseCatalogEntry,
} from "../../contracts/release-catalog";
import { siteBaseUrl } from "../../data/base-url";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; catalog: ReleaseCatalog };

export function DataPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    void loadReleaseCatalog(controller.signal).then(
      (catalog) => setState({ status: "ready", catalog }),
      (error: unknown) => {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : String(error),
          });
        }
      },
    );
    return () => controller.abort();
  }, []);

  if (state.status === "loading") return <p role="status">リリース履歴を読み込んでいます…</p>;
  if (state.status === "error") {
    return <p role="alert">リリース履歴を読み込めませんでした: {state.message}</p>;
  }

  const releases = [...state.catalog.releases].reverse();
  return (
    <section className="data-page">
      <header className="page-heading">
        <p className="eyebrow">Dataset releases</p>
        <h1>Data</h1>
        <p>
          Optimization Compassの公開データを、版・日付・検証用ハッシュから確認できます。
        </p>
      </header>

      <p className="data-current">
        現行版 <strong>v{state.catalog.current_version}</strong>
        <span> · {state.catalog.releases.length} releases</span>
      </p>

      <div
        aria-label="データセットのリリース履歴"
        className="data-table-wrap"
        role="region"
        tabIndex={0}
      >
        <table>
          <caption>公開済みデータセット（新しい順）</caption>
          <thead>
            <tr>
              <th>Version</th>
              <th>公開日</th>
              <th>Size</th>
              <th>SHA-256</th>
              <th>Source</th>
              <th>Bundle</th>
              <th>Archive</th>
            </tr>
          </thead>
          <tbody>
            {releases.map((release) => (
              <ReleaseRow
                current={release.version === state.catalog.current_version}
                key={release.version}
                release={release}
              />
            ))}
          </tbody>
        </table>
      </div>

      <p className="data-note">
        SHA-256は配布物の同一性確認に使えます。Archiveが未登録でも、GitHub Releaseのbundleは取得できます。
      </p>
    </section>
  );
}

function ReleaseRow({ current, release }: { current: boolean; release: ReleaseCatalogEntry }) {
  return (
    <tr>
      <th scope="row">
        <strong>v{release.version}</strong>
        <span className={current ? "data-status data-status-current" : "data-status"}>
          {current ? "現行" : "履歴"}
        </span>
      </th>
      <td><time dateTime={release.release_date}>{release.release_date}</time></td>
      <td title={`${release.bundle.size_bytes.toLocaleString("en-US")} bytes`}>
        {formatBytes(release.bundle.size_bytes)}
      </td>
      <td>
        <details className="data-digest">
          <summary><code>{release.bundle.sha256.slice(0, 12)}…</code></summary>
          <code>{release.bundle.sha256}</code>
        </details>
      </td>
      <td>
        <a href={sourceTagUrl(release.tag)} rel="noreferrer" target="_blank">
          {release.tag}
        </a>
        <details className="data-source">
          <summary>commit <code>{release.source_commit.slice(0, 12)}…</code></summary>
          <a href={sourceCommitUrl(release.source_commit)} rel="noreferrer" target="_blank">
            <code>{release.source_commit}</code>
          </a>
        </details>
      </td>
      <td>
        <a href={release.bundle.url} rel="noreferrer" target="_blank">
          ZIP <span aria-hidden="true">↗</span>
        </a>
      </td>
      <td>
        {release.archival ? (
          <a href={release.archival.url} rel="noreferrer" target="_blank">
            {release.archival.provider} <span aria-hidden="true">↗</span>
          </a>
        ) : <span className="muted">未登録</span>}
      </td>
    </tr>
  );
}

async function loadReleaseCatalog(signal: AbortSignal): Promise<ReleaseCatalog> {
  const base = siteBaseUrl();
  const manifestResponse = await fetch(`${base}data/manifest.json`, { signal });
  if (!manifestResponse.ok) {
    throw new Error(`Manifest request failed (${manifestResponse.status}).`);
  }
  const manifest = parseSiteManifest(await manifestResponse.json());
  const catalogResponse = await fetch(`${base}data/${manifest.release_catalog.path}`, { signal });
  if (!catalogResponse.ok) {
    throw new Error(`Release catalog request failed (${catalogResponse.status}).`);
  }
  const catalog = parseReleaseCatalog(await catalogResponse.json());
  if (catalog.current_version !== manifest.dataset_version) {
    throw new Error("Release catalog current version does not match the manifest.");
  }
  return catalog;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KiB", "MiB", "GiB"];
  let value = bytes / 1024;
  let unit = units[0];
  for (let index = 1; value >= 1024 && index < units.length; index += 1) {
    value /= 1024;
    unit = units[index];
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${unit}`;
}

function sourceTagUrl(tag: string): string {
  return `https://github.com/mryk814/optimization-compass/tree/${tag}`;
}

function sourceCommitUrl(commit: string): string {
  return `https://github.com/mryk814/optimization-compass/commit/${commit}`;
}
