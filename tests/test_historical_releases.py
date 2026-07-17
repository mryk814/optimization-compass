from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import optimization_compass.historical_releases as historical
from optimization_compass.historical_releases import (
    HistoricalBackfillPlan,
    HistoricalReleaseError,
    HistoricalReleasePlanEntry,
    load_historical_backfill_plan,
    reconstruct_historical_release_tree,
    verify_historical_release_tree,
)
from optimization_compass.release_bundle import ReleaseBundle
from optimization_compass.release_catalog import ReleaseBundleDescriptor, ReleaseCatalogEntry
from optimization_compass.repository_boundaries import RepositoryBoundaryError

ROOT = Path(__file__).parents[1]
PLAN = ROOT / "data/releases/historical-backfill.json"


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def _synthetic_release_repo(tmp_path: Path) -> tuple[Path, HistoricalReleasePlanEntry, bytes]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.name", "Historical Test")
    _git(repo, "config", "user.email", "historical@example.com")
    _git(repo, "config", "core.autocrlf", "false")
    version = "0.3.0"
    stem = f"optimization_method_selection_database_v{version}"
    database = b"sqlite-bytes"
    text_lf = b'{\n  "version": "0.3.0"\n}\n'
    text_crlf = text_lf.replace(b"\n", b"\r\n")
    files = {
        f"{stem}.sqlite": {
            "bytes": len(database),
            "sha256": hashlib.sha256(database).hexdigest(),
        },
        f"{stem}.json": {
            "bytes": len(text_crlf),
            "sha256": hashlib.sha256(text_crlf).hexdigest(),
        },
    }
    manifest = {
        "schema_version": 2,
        "version": version,
        "release_date": "2026-07-15",
        "database_sha256": hashlib.sha256(database).hexdigest(),
        "files": files,
    }
    data = repo / "data"
    data.mkdir()
    (data / f"{stem}.sqlite").write_bytes(database)
    (data / f"{stem}.json").write_bytes(text_lf)
    manifest_path = data / f"{stem}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", "-m", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")
    entry = HistoricalReleasePlanEntry(
        version=version,
        release_date="2026-07-15",
        source_commit=commit,
        reconstruction_commit=commit,
        tag="v0.3.0",
        verification_profile="manifest-v2",
        materialization_profile="manifest-crlf-v1",
        manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        database_sha256=hashlib.sha256(database).hexdigest(),
        supplemental_files=(),
    )
    return repo, entry, text_crlf


def test_reviewed_plan_covers_the_exact_historical_set() -> None:
    plan = load_historical_backfill_plan(PLAN)

    assert [entry.version for entry in plan.releases] == [
        "0.2.0",
        "0.3.0",
        "0.3.1",
        "0.3.2",
        "0.4.0",
        "0.5.0",
        "0.5.1",
        "0.6.0",
        "0.7.0",
        "0.8.0",
        "0.9.0",
        "0.10.0",
        "0.11.0",
        "0.12.0",
    ]
    legacy = plan.releases[0]
    assert legacy.source_commit == "1bb71675c418dd6b561c02ba2bbe0fe6a2fdd418"
    assert legacy.reconstruction_commit == "1963561360b08eae4baecf1bd93a903e97658c99"
    assert plan.releases[1].source_commit == "4f0d167d2bba47a7e0342b51b4724852a9a9acd6"
    assert plan.releases[2].source_commit == "ed94b48b67ffbbc34f629f3630a2c696bfa264dd"


def test_existing_historical_tags_resolve_to_catalog_source_commits() -> None:
    plan = load_historical_backfill_plan(PLAN)

    for entry in plan.releases[1:3]:
        assert historical._verify_tag_relationship(ROOT, entry) == entry.source_commit


def test_remote_tag_inventory_peels_annotated_and_keeps_lightweight_tags() -> None:
    annotated_object = "a" * 40
    annotated_commit = "b" * 40
    lightweight_commit = "c" * 40

    targets = historical._parse_remote_tag_targets(
        "\n".join(
            [
                f"{annotated_object}\trefs/tags/v0.3.0",
                f"{annotated_commit}\trefs/tags/v0.3.0^{{}}",
                f"{lightweight_commit}\trefs/tags/v0.3.1",
            ]
        )
    )

    assert targets == {"v0.3.0": annotated_commit, "v0.3.1": lightweight_commit}


@pytest.mark.parametrize(
    "output",
    [
        f"{'a' * 40}\trefs/tags/v0.3.0\n{'b' * 40}\trefs/tags/v0.3.0",
        f"{'b' * 40}\trefs/tags/v0.3.0^{{}}",
    ],
)
def test_remote_tag_inventory_rejects_duplicate_and_orphaned_refs(output: str) -> None:
    with pytest.raises(HistoricalReleaseError, match="duplicate|without direct"):
        historical._parse_remote_tag_targets(output)


def test_remote_tag_lookup_runs_one_explicit_ls_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def run(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        if arguments[3:5] == ["remote", "get-url"]:
            return subprocess.CompletedProcess(
                arguments,
                0,
                stdout="https://github.com/owner/repo.git\n",
                stderr="",
            )
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout=f"{'d' * 40}\trefs/tags/v0.2.0\n",
            stderr="",
        )

    monkeypatch.setattr(historical.subprocess, "run", run)

    assert historical._remote_tag_targets(tmp_path, "origin", "owner/repo") == {"v0.2.0": "d" * 40}
    assert calls == [
        ["git", "-C", str(tmp_path), "remote", "get-url", "--", "origin"],
        ["git", "-C", str(tmp_path), "ls-remote", "--tags", "--", "origin"],
    ]


@pytest.mark.parametrize("remote", ["-upload-pack=evil", "", "origin\nother"])
def test_remote_tag_lookup_rejects_invalid_remote_before_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, remote: str
) -> None:
    monkeypatch.setattr(
        historical.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("git must not run for an invalid remote"),
    )

    with pytest.raises(HistoricalReleaseError, match="remote name is invalid"):
        historical._remote_tag_targets(tmp_path, remote, "owner/repo")


@pytest.mark.parametrize(
    "remote_url",
    [
        "https://github.com/other/repo.git",
        "git@github.com:owner/fork.git",
        "https://example.com/owner/repo.git",
    ],
)
def test_remote_tag_lookup_rejects_a_remote_outside_the_reviewed_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    remote_url: str,
) -> None:
    calls: list[list[str]] = []

    def run(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(arguments)
        return subprocess.CompletedProcess(arguments, 0, stdout=f"{remote_url}\n", stderr="")

    monkeypatch.setattr(historical.subprocess, "run", run)

    with pytest.raises(HistoricalReleaseError, match="reviewed plan"):
        historical._remote_tag_targets(tmp_path, "origin", "owner/repo")

    assert calls == [["git", "-C", str(tmp_path), "remote", "get-url", "--", "origin"]]


@pytest.mark.parametrize("timeout_phase", ["get-url", "ls-remote"])
def test_remote_tag_lookup_fails_on_git_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    timeout_phase: str,
) -> None:
    calls = 0

    def run(arguments: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if timeout_phase == "get-url" or calls == 2:
            raise subprocess.TimeoutExpired(arguments, historical._REMOTE_TIMEOUT_SECONDS)
        return subprocess.CompletedProcess(
            arguments,
            0,
            stdout="https://github.com/owner/repo.git\n",
            stderr="",
        )

    monkeypatch.setattr(historical.subprocess, "run", run)

    with pytest.raises(HistoricalReleaseError, match="timed out"):
        historical._remote_tag_targets(tmp_path, "origin", "owner/repo")


def test_default_remote_opener_uses_a_finite_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, float]] = []
    response = _FakeResponse(b"", "https://github.com/owner/repo")

    def open_url(url: str, *, timeout: float) -> _FakeResponse:
        calls.append((url, timeout))
        return response

    monkeypatch.setattr(historical, "urlopen", open_url)

    assert historical._open_remote_url("https://github.com/owner/repo") is response
    assert calls == [("https://github.com/owner/repo", historical._REMOTE_TIMEOUT_SECONDS)]


@pytest.mark.parametrize(
    ("targets", "message"),
    [({}, "missing"), ({"v0.2.0": "e" * 40}, "differs")],
)
def test_remote_verifier_fails_before_download_for_missing_or_moved_tag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    targets: dict[str, str],
    message: str,
) -> None:
    commit = "d" * 40
    entry = HistoricalReleasePlanEntry(
        version="0.2.0",
        release_date="2026-07-13",
        source_commit=commit,
        reconstruction_commit=commit,
        tag="v0.2.0",
        verification_profile="legacy-v0.2",
        materialization_profile="git-blob-v1",
        manifest_sha256="a" * 64,
        database_sha256="b" * 64,
        supplemental_files=(),
    )
    monkeypatch.setattr(
        historical,
        "load_historical_backfill_plan",
        lambda _path: HistoricalBackfillPlan(1, "owner/repo", (entry,)),
    )
    monkeypatch.setattr(
        historical,
        "load_release_catalog",
        lambda _path: SimpleNamespace(releases=()),
    )
    monkeypatch.setattr(historical, "_remote_tag_targets", lambda *_args: targets)
    opener_called = False

    def opener(_url: str) -> _FakeResponse:
        nonlocal opener_called
        opener_called = True
        return _FakeResponse(b"", "https://github.com/owner/repo")

    with pytest.raises(HistoricalReleaseError, match=message):
        historical.verify_remote_historical_releases(
            tmp_path / "plan.json",
            tmp_path / "catalog.json",
            opener=opener,
        )

    assert not opener_called


def test_git_blob_reconstruction_ignores_checkout_and_uses_declared_crlf(
    tmp_path: Path,
) -> None:
    repo, entry, expected_crlf = _synthetic_release_repo(tmp_path)
    stem = f"optimization_method_selection_database_v{entry.version}"
    (repo / f"data/{stem}.json").write_bytes(b"tampered working tree")

    transformed = reconstruct_historical_release_tree(repo, entry, tmp_path / "release")

    assert transformed == (f"{stem}.json",)
    assert (tmp_path / f"release/{stem}.json").read_bytes() == expected_crlf


def test_undeclared_line_ending_mismatch_is_rejected(tmp_path: Path) -> None:
    repo, entry, _ = _synthetic_release_repo(tmp_path)

    with pytest.raises(HistoricalReleaseError, match="declared materialization"):
        reconstruct_historical_release_tree(
            repo,
            replace(entry, materialization_profile="git-blob-v1"),
            tmp_path / "release",
        )


def test_historical_prepare_uses_shared_guard_with_the_explicit_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other_clone = tmp_path / "other-clone"
    other_clone.mkdir()
    output = tmp_path / "main-worktree" / "bundles"
    calls: list[tuple[Path, Path]] = []

    def reject_output(output_path: Path, *, repository_root: Path) -> Path:
        calls.append((output_path, repository_root))
        raise RepositoryBoundaryError("output must be outside every repository worktree")

    monkeypatch.setattr(historical, "ensure_external_output_path", reject_output)

    with pytest.raises(HistoricalReleaseError, match="outside every repository worktree"):
        historical.prepare_historical_backfill(
            other_clone,
            PLAN,
            tmp_path / "catalog.json",
            output,
        )

    assert calls == [(output, other_clone.resolve())]


def test_real_legacy_profile_reconstructs_manifest_csv_and_license_supplement(
    tmp_path: Path,
) -> None:
    entry = load_historical_backfill_plan(PLAN).releases[0]
    release = tmp_path / "legacy"

    transformed = reconstruct_historical_release_tree(ROOT, entry, release)
    verify_historical_release_tree(release, entry)

    assert transformed == ()
    assert (
        len(list((release / "optimization_method_selection_database_v0.2.0_csv").glob("*.csv")))
        == 33
    )
    assert (release / "licenses/NOTICE.txt").is_file()


def test_existing_tag_source_and_reconstruction_commit_have_identical_release_bytes(
    tmp_path: Path,
) -> None:
    entry = load_historical_backfill_plan(PLAN).releases[1]
    release = tmp_path / "tagged"

    transformed = reconstruct_historical_release_tree(ROOT, entry, release)
    verify_historical_release_tree(release, entry)

    assert entry.source_commit == "4f0d167d2bba47a7e0342b51b4724852a9a9acd6"
    assert entry.reconstruction_commit == "1963561360b08eae4baecf1bd93a903e97658c99"
    assert f"optimization_method_selection_database_v{entry.version}.json" in transformed


@pytest.mark.parametrize(
    ("expected_bytes", "expected_sha256", "message"),
    [
        (4, hashlib.sha256(b"zip").hexdigest(), "size"),
        (3, "0" * 64, "digest"),
    ],
)
def test_cataloged_bundle_rejects_outer_byte_mismatch_before_inner_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    expected_bytes: int,
    expected_sha256: str,
    message: str,
) -> None:
    bundle_path = tmp_path / "optimization_method_selection_database_v0.2.0_bundle.zip"
    bundle_path.write_bytes(b"zip")
    plan_entry = load_historical_backfill_plan(PLAN).releases[0]
    catalog_entry = ReleaseCatalogEntry(
        version=plan_entry.version,
        release_date=plan_entry.release_date,
        database_sha256=plan_entry.database_sha256,
        manifest_sha256=plan_entry.manifest_sha256,
        source_commit=plan_entry.source_commit,
        tag=plan_entry.tag,
        bundle=ReleaseBundleDescriptor(
            url=f"https://github.com/owner/repo/releases/download/v0.2.0/{bundle_path.name}",
            sha256=expected_sha256,
            size_bytes=expected_bytes,
        ),
        archival=None,
    )
    monkeypatch.setattr(
        historical,
        "load_release_catalog",
        lambda _path: SimpleNamespace(releases=(catalog_entry,)),
    )
    monkeypatch.setattr(
        historical,
        "verify_historical_release_bundle",
        lambda *_args: pytest.fail("inner verification must wait for exact outer bytes"),
    )

    with pytest.raises(HistoricalReleaseError, match=message):
        historical.verify_cataloged_historical_release_bundle(
            bundle_path, plan_entry, tmp_path / "candidate.json", "owner/repo"
        )


def test_cataloged_bundle_rejects_catalog_provenance_mismatch_before_inner_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_path = tmp_path / "optimization_method_selection_database_v0.2.0_bundle.zip"
    bundle_path.write_bytes(b"zip")
    plan_entry = load_historical_backfill_plan(PLAN).releases[0]
    catalog_entry = ReleaseCatalogEntry(
        version=plan_entry.version,
        release_date=plan_entry.release_date,
        database_sha256=plan_entry.database_sha256,
        manifest_sha256=plan_entry.manifest_sha256,
        source_commit="f" * 40,
        tag=plan_entry.tag,
        bundle=ReleaseBundleDescriptor(
            url=f"https://github.com/owner/repo/releases/download/v0.2.0/{bundle_path.name}",
            sha256=hashlib.sha256(b"zip").hexdigest(),
            size_bytes=3,
        ),
        archival=None,
    )
    monkeypatch.setattr(
        historical,
        "load_release_catalog",
        lambda _path: SimpleNamespace(releases=(catalog_entry,)),
    )
    monkeypatch.setattr(
        historical,
        "verify_historical_release_bundle",
        lambda *_args: pytest.fail("inner verification must wait for provenance"),
    )

    with pytest.raises(HistoricalReleaseError, match="provenance differs"):
        historical.verify_cataloged_historical_release_bundle(
            bundle_path, plan_entry, tmp_path / "candidate.json", "owner/repo"
        )


def test_batch_prepare_removes_transaction_after_mid_batch_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit = "1" * 40
    entries = tuple(
        HistoricalReleasePlanEntry(
            version=version,
            release_date="2026-07-15",
            source_commit=commit,
            reconstruction_commit=commit,
            tag=f"v{version}",
            verification_profile="manifest-v2",
            materialization_profile="git-blob-v1",
            manifest_sha256="a" * 64,
            database_sha256="b" * 64,
            supplemental_files=(),
        )
        for version in ("0.2.0", "0.3.0")
    )
    monkeypatch.setattr(
        historical,
        "load_historical_backfill_plan",
        lambda _path: HistoricalBackfillPlan(1, "owner/repo", entries),
    )
    calls = 0

    def reconstruct(
        _root: Path, entry: HistoricalReleasePlanEntry, output: Path
    ) -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise HistoricalReleaseError("injected batch failure")
        output.mkdir(parents=True)
        return ()

    first_bundle = tmp_path / "first.zip"
    first_bundle.write_bytes(b"zip")
    bundle = ReleaseBundle(
        "0.2.0", "2026-07-15", "v0.2.0", commit, first_bundle, 3, "c" * 64, "a" * 64
    )
    monkeypatch.setattr(historical, "reconstruct_historical_release_tree", reconstruct)
    monkeypatch.setattr(historical, "verify_historical_release_tree", lambda *_args: None)
    monkeypatch.setattr(historical, "_verify_tag_relationship", lambda *_args: None)
    monkeypatch.setattr(historical, "_build_preverified_release_bundle", lambda *_a, **_k: bundle)
    monkeypatch.setattr(historical, "verify_historical_release_bundle", lambda *_a: bundle)
    output = tmp_path / "outside" / "batch"

    with pytest.raises(HistoricalReleaseError, match="injected batch failure"):
        historical.prepare_historical_backfill(ROOT, PLAN, Path("unused"), output)

    assert not output.exists()
    assert not list(output.parent.glob(f".{output.name}.*"))


class _FakeResponse:
    def __init__(self, content: bytes, final_url: str) -> None:
        self._content = content
        self._offset = 0
        self._final_url = final_url
        self.headers = {"Content-Length": str(len(content))}

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def geturl(self) -> str:
        return self._final_url

    def read(self, amount: int = -1) -> bytes:
        if amount < 0:
            amount = len(self._content)
        chunk = self._content[self._offset : self._offset + amount]
        self._offset += len(chunk)
        return chunk


def test_remote_download_accepts_only_exact_bytes_and_approved_redirect(tmp_path: Path) -> None:
    content = b"bundle bytes"
    destination = tmp_path / "bundle.zip"

    historical._download_exact_bundle(
        "https://github.com/owner/repo/releases/download/v0.2.0/bundle.zip",
        destination,
        expected_bytes=len(content),
        expected_sha256=hashlib.sha256(content).hexdigest(),
        opener=lambda _url: _FakeResponse(
            content, "https://release-assets.githubusercontent.com/object"
        ),
    )

    assert destination.read_bytes() == content


@pytest.mark.parametrize(
    ("final_url", "expected_sha", "message"),
    [
        ("https://example.com/object", hashlib.sha256(b"bundle bytes").hexdigest(), "host"),
        ("https://release-assets.githubusercontent.com/object", "0" * 64, "digest"),
    ],
)
def test_remote_download_rejects_redirect_and_digest_failures(
    tmp_path: Path, final_url: str, expected_sha: str, message: str
) -> None:
    destination = tmp_path / "bundle.zip"

    with pytest.raises(HistoricalReleaseError, match=message):
        historical._download_exact_bundle(
            "https://github.com/owner/repo/releases/download/v0.2.0/bundle.zip",
            destination,
            expected_bytes=len(b"bundle bytes"),
            expected_sha256=expected_sha,
            opener=lambda _url: _FakeResponse(b"bundle bytes", final_url),
        )

    assert not destination.exists()
