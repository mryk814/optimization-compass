from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest

import optimization_compass.release_bundle as release_bundle_module
from optimization_compass.dataset_release import build_staged_release
from optimization_compass.release_bundle import (
    ReleaseBundleError,
    build_release_bundle,
    verify_release_bundle,
)
from optimization_compass.repository_boundaries import RepositoryBoundaryError

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"
SOURCE_COMMIT = "1" * 40


@pytest.fixture(scope="module")
def staged_release(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("bundle-release")
    return build_staged_release(
        BASE_DATABASE,
        root / "staged",
        target_version="0.3.0",
        release_date="2026-07-14",
    ).output_directory


def test_complete_bundle_is_byte_deterministic_and_self_verifying(
    staged_release: Path, tmp_path: Path
) -> None:
    first = build_release_bundle(
        staged_release,
        tmp_path / "first",
        source_commit=SOURCE_COMMIT,
        tag="v0.3.0",
    )
    second = build_release_bundle(
        staged_release,
        tmp_path / "second",
        source_commit=SOURCE_COMMIT,
        tag="v0.3.0",
    )

    assert first.sha256 == second.sha256
    assert first.path.read_bytes() == second.path.read_bytes()
    verified = verify_release_bundle(first.path)
    assert verified == first


def test_bundle_verification_rejects_tampered_member(staged_release: Path, tmp_path: Path) -> None:
    original = build_release_bundle(
        staged_release,
        tmp_path / "original",
        source_commit=SOURCE_COMMIT,
        tag="v0.3.0",
    ).path
    tampered = tmp_path / "tampered.zip"
    with (
        zipfile.ZipFile(original) as source,
        zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as target,
    ):
        for member in source.infolist():
            content = source.read(member.filename)
            if member.filename.endswith("_report.md"):
                content += b"tampered"
            target.writestr(member, content)

    with pytest.raises(ReleaseBundleError, match="size differs"):
        verify_release_bundle(tampered)


def test_bundle_verification_binds_index_to_canonical_manifest(
    staged_release: Path, tmp_path: Path
) -> None:
    original = build_release_bundle(
        staged_release,
        tmp_path / "original-manifest",
        source_commit=SOURCE_COMMIT,
        tag="v0.3.0",
    ).path
    tampered = tmp_path / "manifest-substitution.zip"
    with (
        zipfile.ZipFile(original) as source,
        zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as target,
    ):
        index = release_bundle_module.json.loads(source.read("bundle-index.json"))
        report_relative = next(name for name in index["files"] if name.endswith("_report.md"))
        index["manifest"] = {"path": report_relative, **index["files"][report_relative]}
        for member in source.infolist():
            content = source.read(member.filename)
            if member.filename == "bundle-index.json":
                content = release_bundle_module._canonical_json(index)
            target.writestr(member, content)

    with pytest.raises(ReleaseBundleError, match="canonical versioned manifest"):
        verify_release_bundle(tampered)


def test_bundle_write_failure_removes_partial_archive_and_allows_retry(
    staged_release: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "write-failure"
    archive = output / "optimization_method_selection_database_v0.3.0_bundle.zip"
    real_write = release_bundle_module._write_zip_member
    writes = 0

    def fail_after_first_member(
        target: zipfile.ZipFile,
        name: str,
        content: bytes,
        timestamp: tuple[int, int, int, int, int, int],
    ) -> None:
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("injected ZIP write failure")
        real_write(target, name, content, timestamp)

    monkeypatch.setattr(release_bundle_module, "_write_zip_member", fail_after_first_member)
    with pytest.raises(OSError, match="injected ZIP write failure"):
        build_release_bundle(
            staged_release,
            output,
            source_commit=SOURCE_COMMIT,
            tag="v0.3.0",
        )
    assert not archive.exists()

    monkeypatch.setattr(release_bundle_module, "_write_zip_member", real_write)
    retried = build_release_bundle(
        staged_release,
        output,
        source_commit=SOURCE_COMMIT,
        tag="v0.3.0",
    )
    assert retried.path == archive
    assert verify_release_bundle(archive) == retried


@pytest.mark.parametrize(
    ("source_commit", "tag", "message"),
    [
        ("short", "v0.3.0", "source commit"),
        (SOURCE_COMMIT, "dataset-v0.3.0", "release tag"),
    ],
)
def test_bundle_build_requires_explicit_unambiguous_source_identity(
    staged_release: Path,
    tmp_path: Path,
    source_commit: str,
    tag: str,
    message: str,
) -> None:
    with pytest.raises(ReleaseBundleError, match=message):
        build_release_bundle(
            staged_release,
            tmp_path / f"invalid-{tag}",
            source_commit=source_commit,
            tag=tag,
        )


def test_bundle_verification_rejects_corrupt_zip(staged_release: Path, tmp_path: Path) -> None:
    bundle = build_release_bundle(
        staged_release,
        tmp_path / "valid",
        source_commit=SOURCE_COMMIT,
        tag="v0.3.0",
    ).path
    corrupt = tmp_path / "corrupt.zip"
    shutil.copy2(bundle, corrupt)
    corrupt.write_bytes(corrupt.read_bytes()[:100])

    with pytest.raises(ReleaseBundleError, match="invalid"):
        verify_release_bundle(corrupt)


def test_bundle_build_rejects_output_inside_repository(staged_release: Path) -> None:
    with pytest.raises(ReleaseBundleError, match="outside every repository worktree"):
        build_release_bundle(
            staged_release,
            ROOT / ".release-bundle-test",
            source_commit=SOURCE_COMMIT,
            tag="v0.3.0",
        )


def test_preverified_bundle_uses_shared_guard_with_the_explicit_repository_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository_root = tmp_path / "secondary-worktree"
    output = tmp_path / "main-worktree" / "bundle"
    calls: list[tuple[Path, Path]] = []

    def reject_output(output_path: Path, *, repository_root: Path) -> Path:
        calls.append((output_path, repository_root))
        raise RepositoryBoundaryError("output must be outside every repository worktree")

    monkeypatch.setattr(release_bundle_module, "ensure_external_output_path", reject_output)

    with pytest.raises(ReleaseBundleError, match="outside every repository worktree"):
        release_bundle_module._build_preverified_release_bundle(
            tmp_path / "release-tree",
            output,
            version="0.3.0",
            release_date="2026-07-17",
            source_commit=SOURCE_COMMIT,
            tag="v0.3.0",
            manifest_path=tmp_path / "release-tree/manifest.json",
            repository_root=repository_root,
        )

    assert calls == [(output, repository_root)]
