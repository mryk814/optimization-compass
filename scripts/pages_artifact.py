from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit
from urllib.request import Request, urlopen

HASH_ROUTES = (
    "/",
    "/#/map",
    "/#/diagnose",
    "/#/theater/nelder-mead",
    "/#/gallery",
    "/#/coverage",
    "/#/search?q=BO&type=method",
)
JSON_ASSETS = (
    "data/release.json",
    "data/manifest.json",
    "data/views/problem-structure.json",
    "data/content.json",
    "data/gallery.json",
    "data/comparisons.json",
    "data/traces/index.json",
    "data/coverage.json",
    "data/search-index.json",
    "data/retrieval-documents.json",
    "data/search-benchmark.json",
)
DEPLOYMENT_FIELDS = {
    "schema_version",
    "commit_sha",
    "dataset_version",
    "release_date",
    "database_sha256",
    "base_path",
}


class PagesArtifactError(ValueError):
    pass


@dataclass(frozen=True)
class DeploymentIdentity:
    schema_version: int
    commit_sha: str
    dataset_version: str
    release_date: str
    database_sha256: str
    base_path: str


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script" and attributes.get("src"):
            self.references.append(str(attributes["src"]))
        if tag == "link" and attributes.get("href"):
            self.references.append(str(attributes["href"]))


def stamp_artifact(root: Path, commit_sha: str, base_path: str) -> DeploymentIdentity:
    release = _read_json_file(root / "data/release.json")
    identity = DeploymentIdentity(
        schema_version=1,
        commit_sha=_commit_sha(commit_sha),
        dataset_version=_semantic_version(release.get("dataset_version"), "dataset version"),
        release_date=_release_date(release.get("release_date")),
        database_sha256=_sha256(release.get("database_sha256"), "database SHA-256"),
        base_path=_base_path(base_path),
    )
    destination = root / "deployment.json"
    destination.write_text(
        json.dumps(asdict(identity), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    verify_local_artifact(root, commit_sha=identity.commit_sha)
    return identity


def verify_local_artifact(
    root: Path,
    *,
    commit_sha: str | None = None,
    dataset_version: str | None = None,
) -> dict[str, object]:
    identity = _deployment_identity(_read_json_file(root / "deployment.json"))
    _verify_expected_identity(identity, commit_sha=commit_sha, dataset_version=dataset_version)
    _verify_release_matches_deployment(_read_json_file(root / "data/release.json"), identity)
    index = (root / "index.html").read_text(encoding="utf-8")
    references = _verify_html(index, identity.base_path)
    for reference in references:
        relative = reference.removeprefix(identity.base_path)
        target = (root / relative).resolve()
        if root.resolve() not in target.parents or not target.is_file():
            raise PagesArtifactError(f"HTML asset does not resolve inside artifact: {reference}")
    assets = _verify_json_assets(
        lambda relative: _read_json_file(root / relative), identity.dataset_version
    )
    manifest = _read_json_file(root / "data/manifest.json")
    license_paths = _license_paths(manifest)
    for relative in license_paths:
        target = (root / relative).resolve()
        if root.resolve() not in target.parents or not target.is_file() or not target.read_bytes():
            raise PagesArtifactError(f"site license path does not resolve: {relative}")
    return {
        "commit_sha": identity.commit_sha,
        "dataset_version": identity.dataset_version,
        "routes": list(HASH_ROUTES),
        "json_assets": assets,
        "license_paths": license_paths,
        "html_assets": references,
    }


def smoke_remote_artifact(
    base_url: str,
    *,
    commit_sha: str,
    dataset_version: str,
    attempts: int = 10,
    delay_seconds: float = 6,
    timeout_seconds: float = 20,
) -> dict[str, object]:
    if attempts < 1:
        raise PagesArtifactError("attempts must be at least one")
    if delay_seconds < 0 or timeout_seconds <= 0:
        raise PagesArtifactError("retry delay and timeout must be valid")
    normalized_base = _base_url(base_url)
    expected_commit = _commit_sha(commit_sha)
    expected_version = _semantic_version(dataset_version, "expected dataset version")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _smoke_remote_once(
                normalized_base,
                commit_sha=expected_commit,
                dataset_version=expected_version,
                timeout_seconds=timeout_seconds,
            )
        except (PagesArtifactError, HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
            print(f"Pages smoke attempt {attempt}/{attempts} failed: {error}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(delay_seconds)
    raise PagesArtifactError(f"deployed Pages artifact did not converge: {last_error}")


def _smoke_remote_once(
    base_url: str,
    *,
    commit_sha: str,
    dataset_version: str,
    timeout_seconds: float,
) -> dict[str, object]:
    cache_query = f"?commit={commit_sha}"
    identity = _deployment_identity(
        _read_remote_json(urljoin(base_url, "deployment.json") + cache_query, timeout_seconds)
    )
    _verify_expected_identity(identity, commit_sha=commit_sha, dataset_version=dataset_version)
    _verify_release_matches_deployment(
        _read_remote_json(urljoin(base_url, "data/release.json") + cache_query, timeout_seconds),
        identity,
    )
    route_urls: list[str] = []
    for route in HASH_ROUTES:
        public_url = base_url.rstrip("/") + route
        fetch_url = urldefrag(public_url).url
        html = _fetch(fetch_url + cache_query, timeout_seconds).decode("utf-8")
        _verify_html(html, identity.base_path)
        route_urls.append(public_url)
    assets = _verify_json_assets(
        lambda relative: _read_remote_json(
            urljoin(base_url, relative) + cache_query, timeout_seconds
        ),
        identity.dataset_version,
    )
    manifest = _read_remote_json(
        urljoin(base_url, "data/manifest.json") + cache_query, timeout_seconds
    )
    license_paths = _license_paths(manifest)
    for relative in license_paths:
        if not _fetch(urljoin(base_url, relative) + cache_query, timeout_seconds):
            raise PagesArtifactError(f"deployed license is empty: {relative}")
    return {
        "base_url": base_url,
        "commit_sha": identity.commit_sha,
        "dataset_version": identity.dataset_version,
        "routes": route_urls,
        "json_assets": assets,
        "license_paths": license_paths,
    }


def _verify_json_assets(
    loader: Any,
    dataset_version: str,
) -> list[str]:
    for relative in JSON_ASSETS:
        payload = loader(relative)
        if payload.get("dataset_version") != dataset_version:
            raise PagesArtifactError(f"dataset version mismatch in {relative}")
    return list(JSON_ASSETS)


def _verify_html(index: str, base_path: str) -> list[str]:
    if '<div id="root"></div>' not in index:
        raise PagesArtifactError("Pages index does not contain the application root")
    parser = _AssetReferenceParser()
    parser.feed(index)
    references = sorted(
        {reference for reference in parser.references if not reference.startswith("data:")}
    )
    if not references:
        raise PagesArtifactError("Pages index does not reference a built asset")
    for reference in references:
        parts = urlsplit(reference)
        if parts.scheme or parts.netloc or not parts.path.startswith(base_path):
            raise PagesArtifactError(f"HTML asset is outside configured base path: {reference}")
        _safe_relative(parts.path.removeprefix(base_path), "HTML asset")
    return references


def _license_paths(manifest: dict[str, Any]) -> list[str]:
    licenses = manifest.get("licenses")
    if not isinstance(licenses, dict):
        raise PagesArtifactError("site manifest does not declare licenses")
    paths: list[str] = []
    for scope in ("code", "data", "content"):
        entry = licenses.get(scope)
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise PagesArtifactError(f"site manifest license is invalid: {scope}")
        paths.append(_safe_relative(entry["path"], f"licenses.{scope}.path"))
    for field in ("legal_code_path", "notice_path"):
        value = licenses.get(field)
        if not isinstance(value, str):
            raise PagesArtifactError(f"site manifest license is invalid: {field}")
        paths.append(_safe_relative(value, f"licenses.{field}"))
    return sorted(set(paths))


def _deployment_identity(payload: dict[str, Any]) -> DeploymentIdentity:
    if set(payload) != DEPLOYMENT_FIELDS or payload.get("schema_version") != 1:
        raise PagesArtifactError("deployment identity does not match schema version 1")
    return DeploymentIdentity(
        schema_version=1,
        commit_sha=_commit_sha(payload.get("commit_sha")),
        dataset_version=_semantic_version(payload.get("dataset_version"), "dataset version"),
        release_date=_release_date(payload.get("release_date")),
        database_sha256=_sha256(payload.get("database_sha256"), "database SHA-256"),
        base_path=_base_path(payload.get("base_path")),
    )


def _verify_expected_identity(
    identity: DeploymentIdentity,
    *,
    commit_sha: str | None,
    dataset_version: str | None,
) -> None:
    if commit_sha is not None and identity.commit_sha != _commit_sha(commit_sha):
        raise PagesArtifactError("deployment commit SHA does not match validated commit")
    if dataset_version is not None and identity.dataset_version != _semantic_version(
        dataset_version, "expected dataset version"
    ):
        raise PagesArtifactError("deployment dataset version does not match validated dataset")


def _verify_release_matches_deployment(
    release: dict[str, Any], identity: DeploymentIdentity
) -> None:
    if release.get("schema_version") != 1:
        raise PagesArtifactError("release identity does not match schema version 1")
    expected = {
        "dataset_version": identity.dataset_version,
        "release_date": identity.release_date,
        "database_sha256": identity.database_sha256,
    }
    for field, value in expected.items():
        if release.get(field) != value:
            raise PagesArtifactError(f"deployment identity differs from data/release.json: {field}")


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PagesArtifactError(f"JSON asset is unreadable: {path}") from error
    if not isinstance(payload, dict):
        raise PagesArtifactError(f"JSON asset must be an object: {path}")
    return payload


def _read_remote_json(url: str, timeout_seconds: float) -> dict[str, Any]:
    try:
        payload = json.loads(_fetch(url, timeout_seconds))
    except json.JSONDecodeError as error:
        raise PagesArtifactError(f"deployed JSON asset is invalid: {url}") from error
    if not isinstance(payload, dict):
        raise PagesArtifactError(f"deployed JSON asset must be an object: {url}")
    return payload


def _fetch(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={"Cache-Control": "no-cache", "User-Agent": "optimization-compass-pages-smoke/1"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        if response.status != 200:
            raise PagesArtifactError(f"deployed asset returned HTTP {response.status}: {url}")
        return response.read()


def _safe_relative(value: str, field: str) -> str:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise PagesArtifactError(f"{field} is not a safe relative path")
    return value


def _commit_sha(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise PagesArtifactError("commit SHA must be 40 lowercase hexadecimal characters")
    return value


def _semantic_version(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value) is None:
        raise PagesArtifactError(f"{field} must be semantic version X.Y.Z")
    return value


def _release_date(value: object) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise PagesArtifactError("release date must be YYYY-MM-DD")
    return value


def _sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise PagesArtifactError(f"{field} is invalid")
    return value


def _base_path(value: object) -> str:
    if not isinstance(value, str) or not value.startswith("/") or not value.endswith("/"):
        raise PagesArtifactError("base path must begin and end with a slash")
    if "//" in value or ".." in Path(value).parts:
        raise PagesArtifactError("base path is invalid")
    return value


def _base_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.query or parts.fragment:
        raise PagesArtifactError("base URL must be an HTTP(S) URL without query or fragment")
    return value.rstrip("/") + "/"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stamp and verify one validated Pages artifact.")
    commands = parser.add_subparsers(dest="command", required=True)
    stamp = commands.add_parser("stamp", help="Write deployment.json into a built artifact.")
    stamp.add_argument("--root", type=Path, required=True)
    stamp.add_argument("--commit-sha", required=True)
    stamp.add_argument("--base-path", default="/optimization-compass/")
    local = commands.add_parser("verify-local", help="Verify a built Pages artifact directory.")
    local.add_argument("--root", type=Path, required=True)
    local.add_argument("--expected-commit-sha")
    local.add_argument("--expected-dataset-version")
    remote = commands.add_parser("smoke-remote", help="Verify the deployed Pages artifact.")
    remote.add_argument("--base-url", required=True)
    remote.add_argument("--expected-commit-sha", required=True)
    remote.add_argument("--expected-dataset-version", required=True)
    remote.add_argument("--attempts", type=int, default=10)
    remote.add_argument("--delay-seconds", type=float, default=6)
    remote.add_argument("--timeout-seconds", type=float, default=20)
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        if args.command == "stamp":
            result: object = asdict(stamp_artifact(args.root, args.commit_sha, args.base_path))
        elif args.command == "verify-local":
            result = verify_local_artifact(
                args.root,
                commit_sha=args.expected_commit_sha,
                dataset_version=args.expected_dataset_version,
            )
        else:
            result = smoke_remote_artifact(
                args.base_url,
                commit_sha=args.expected_commit_sha,
                dataset_version=args.expected_dataset_version,
                attempts=args.attempts,
                delay_seconds=args.delay_seconds,
                timeout_seconds=args.timeout_seconds,
            )
    except PagesArtifactError as error:
        parser.exit(1, f"Pages artifact verification failed: {error}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
