from __future__ import annotations

import json
import os
import shutil
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest
from filelock import FileLock

from optimization_compass.dataset_release import (
    DATASET_STEM,
    RELEASE_DATE,
    TARGET_DATASET_VERSION,
    StagedRelease,
    build_staged_release,
    tree_hash,
)
from optimization_compass.db import KnowledgeRepository
from optimization_compass.engine import RecommendationEngine
from optimization_compass.site_export import export_site_data
from optimization_compass.view_spec import SiteManifest

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"
RUNTIME_DATABASE = ROOT / "src/optimization_compass/resources/knowledge.sqlite"


@pytest.fixture(scope="session")
def database_path() -> Path:
    return RUNTIME_DATABASE


@pytest.fixture()
def repository(database_path: Path) -> KnowledgeRepository:
    return KnowledgeRepository(database_path)


@pytest.fixture()
def engine(repository: KnowledgeRepository) -> RecommendationEngine:
    return RecommendationEngine(repository)


# Staging a release (about 40 s) and exporting the site (about 30 s) used to run once per
# test, which made the full suite take 51 minutes. The builds are deterministic, so each
# distinct artifact is now built once per run and shared. Under pytest-xdist the workers
# share one copy through a file lock instead of each building their own.


class SharedArtifacts:
    """Directories built once per test run and handed out read-only.

    Each built tree's hash is recorded when it is built and checked again when the session
    ends, so a test that writes into a shared tree fails the run instead of silently
    changing what later tests see. Tests that mutate must take a private copy.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self._used: dict[Path, str] = {}

    def directory(self, key: str, build: Callable[[Path], None]) -> Path:
        target = self.root / key
        marker = self.root / f"{key}.sha256"
        with FileLock(str(self.root / f"{key}.lock")):
            if not marker.exists():
                # A worker that died mid-build leaves a tree without a marker.
                if target.exists():
                    shutil.rmtree(target)
                build(target)
                marker.write_text(tree_hash(target), encoding="utf-8")
        self._used[target] = marker.read_text(encoding="utf-8")
        return target

    def assert_unchanged(self) -> None:
        changed = [
            path.name for path, expected in self._used.items() if tree_hash(path) != expected
        ]
        assert not changed, (
            f"tests wrote into shared read-only artifacts {changed}; "
            "use a private copy (staged_releases.copy) instead"
        )


@pytest.fixture(scope="session")
def shared_artifacts(tmp_path_factory: pytest.TempPathFactory) -> Iterator[SharedArtifacts]:
    if os.environ.get("PYTEST_XDIST_WORKER"):
        # Every worker's basetemp sits in the same per-run directory.
        root = tmp_path_factory.getbasetemp().parent / "shared-artifacts"
    else:
        root = tmp_path_factory.getbasetemp() / "shared-artifacts"
    root.mkdir(parents=True, exist_ok=True)
    artifacts = SharedArtifacts(root)
    yield artifacts
    artifacts.assert_unchanged()


def _staged_release_at(directory: Path) -> StagedRelease:
    """Describe a staged release tree, as build_staged_release would for that directory."""
    manifest_path = next(directory.glob("*_manifest.json"))
    version = str(json.loads(manifest_path.read_text(encoding="utf-8"))["version"])
    stem = DATASET_STEM.format(version=version)
    return StagedRelease(
        version=version,
        output_directory=directory,
        database_path=directory / f"{stem}.sqlite",
        manifest_path=manifest_path,
        release_identity_path=directory / f"{stem}_release.json",
        site_data_directory=directory / f"{stem}_site-data",
        tree_sha256=tree_hash(directory),
    )


class StagedReleases:
    """Releases staged from the pinned base database, one per (version, date)."""

    def __init__(self, artifacts: SharedArtifacts) -> None:
        self._artifacts = artifacts

    def shared(
        self,
        target_version: str = TARGET_DATASET_VERSION,
        release_date: str = RELEASE_DATE,
    ) -> StagedRelease:
        """The shared tree. Read it only; use copy() to change anything in it."""

        def build(output: Path) -> None:
            build_staged_release(
                BASE_DATABASE,
                output,
                target_version=target_version,
                release_date=release_date,
            )

        directory = self._artifacts.directory(f"staged-{target_version}-{release_date}", build)
        return _staged_release_at(directory)

    def copy(
        self,
        destination: Path,
        target_version: str = TARGET_DATASET_VERSION,
        release_date: str = RELEASE_DATE,
    ) -> StagedRelease:
        """A private copy at destination, byte-identical to a fresh stage there."""
        shared = self.shared(target_version, release_date)
        shutil.copytree(shared.output_directory, destination)
        return _staged_release_at(destination)


@pytest.fixture(scope="session")
def staged_releases(shared_artifacts: SharedArtifacts) -> StagedReleases:
    return StagedReleases(shared_artifacts)


@pytest.fixture(scope="session")
def staged_release(staged_releases: StagedReleases) -> StagedRelease:
    """The default staged release, shared read-only across the session."""
    return staged_releases.shared()


@dataclass(frozen=True)
class SiteExportPair:
    """Two independent exports of the runtime database, for determinism checks."""

    first: Path
    second: Path
    first_manifest: SiteManifest
    second_manifest: SiteManifest


@pytest.fixture(scope="session")
def site_export_pair(shared_artifacts: SharedArtifacts) -> SiteExportPair:
    """Read-only: tests that patch the exporter's inputs must export on their own."""

    def build(output: Path) -> None:
        output.mkdir()
        for name in ("first", "second"):
            manifest = export_site_data(output / name, KnowledgeRepository(RUNTIME_DATABASE))
            (output / f"{name}-returned-manifest.json").write_text(
                manifest.model_dump_json(), encoding="utf-8"
            )

    directory = shared_artifacts.directory("site-export-pair", build)
    return SiteExportPair(
        first=directory / "first",
        second=directory / "second",
        first_manifest=SiteManifest.model_validate_json(
            (directory / "first-returned-manifest.json").read_bytes()
        ),
        second_manifest=SiteManifest.model_validate_json(
            (directory / "second-returned-manifest.json").read_bytes()
        ),
    )
