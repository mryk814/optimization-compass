from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "repository_size.py"
SPEC = importlib.util.spec_from_file_location("repository_size_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REPOSITORY_SIZE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPOSITORY_SIZE
SPEC.loader.exec_module(REPOSITORY_SIZE)

RepositorySizePolicy = REPOSITORY_SIZE.RepositorySizePolicy
collect_repository_size = REPOSITORY_SIZE.collect_repository_size
release_distribution_version = REPOSITORY_SIZE.release_distribution_version
EMPTY_CATALOG = b'{"current_version":null,"releases":[],"schema_version":1}'


def _git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", "-C", str(repo), *arguments], check=True, capture_output=True)


def _repository(tmp_path: Path, files: dict[str, bytes]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    for relative_path, content in files.items():
        path = repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    _git(repo, "add", ".")
    return repo


def test_report_counts_tracked_checkout_data_and_release_distribution(tmp_path: Path) -> None:
    repo = _repository(
        tmp_path,
        {
            "README.md": b"readme",
            "data/README.md": b"data",
            "data/optimization_method_selection_database_v0.12.0.json": b"distribution",
            "data/optimization_method_selection_database_v0.12.0_release.json": b"compact",
        },
    )
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), len(b"distribution"))

    report = collect_repository_size(repo, policy)

    assert report.tracked_file_count == 4
    assert report.tracked_working_tree_bytes == len(b"readmedatadistributioncompact")
    assert report.data_tracked_file_count == 3
    assert report.data_working_tree_bytes == len(b"datadistributioncompact")
    assert report.release_distribution_file_count == 1
    assert report.release_distribution_git_blob_bytes == len(b"distribution")
    assert report.violations == ()


def test_gate_rejects_new_release_distribution_but_allows_compact_metadata(
    tmp_path: Path,
) -> None:
    repo = _repository(
        tmp_path,
        {
            "data/optimization_method_selection_database_v0.13.0.sqlite": b"bundle",
            "data/optimization_method_selection_database_v0.13.0_manifest.json": b"manifest",
            "data/optimization_method_selection_database_v0.13.0_release.json": b"identity",
            "data/optimization_method_selection_database_v0.13.0_report.md": b"report",
            "data/optimization_method_selection_database_v0.13.0_schema.sql": b"schema",
        },
    )
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), 0)

    report = collect_repository_size(repo, policy)

    assert [violation.code for violation in report.violations] == [
        "new_tracked_release_distribution"
    ]
    assert report.violations[0].path is not None
    assert report.violations[0].path.endswith("v0.13.0.sqlite")


def test_gate_rejects_growth_inside_a_grandfathered_release(tmp_path: Path) -> None:
    repo = _repository(
        tmp_path,
        {"data/optimization_method_selection_database_v0.12.0.json": b"too large"},
    )
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), len(b"too large") - 1)

    report = collect_repository_size(repo, policy)

    assert [violation.code for violation in report.violations] == [
        "historical_release_distribution_growth"
    ]


def test_distribution_classifier_excludes_only_compact_release_metadata() -> None:
    prefix = "data/optimization_method_selection_database_v0.13.0"

    assert release_distribution_version(f"{prefix}.json") == "0.13.0"
    assert release_distribution_version(f"{prefix}_csv/table.csv") == "0.13.0"
    assert release_distribution_version(f"{prefix}_schema.sql") is None
    assert release_distribution_version(f"{prefix}_manifest.json") is None
    assert release_distribution_version(f"{prefix}_release.json") is None
    assert release_distribution_version(f"{prefix}_report.md") is None
    assert release_distribution_version("data/seeds/site_gallery.json") is None


def test_default_policy_retains_only_pinned_legacy_sqlite() -> None:
    assert REPOSITORY_SIZE.HISTORICAL_RELEASE_VERSIONS == frozenset({"0.2.0"})
    assert REPOSITORY_SIZE.HISTORICAL_RELEASE_DISTRIBUTION_BASELINE_BYTES == 3_506_176
    assert (
        release_distribution_version(
            "data/optimization_method_selection_database_v0.2.0.sqlite"
        )
        == "0.2.0"
    )


def test_gate_rejects_bundle_moved_under_compact_release_directory(tmp_path: Path) -> None:
    repo = _repository(
        tmp_path,
        {
            "data/releases/catalog.json": EMPTY_CATALOG,
            "data/releases/v0.13.0/complete-bundle.zip": b"renamed bundle",
        },
    )
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), 0)

    report = collect_repository_size(repo, policy)

    assert [(item.code, item.path) for item in report.violations] == [
        ("disallowed_tracked_archive", "data/releases/v0.13.0/complete-bundle.zip")
    ]


def test_gate_rejects_renamed_large_distribution_blob(tmp_path: Path) -> None:
    repo = _repository(
        tmp_path,
        {
            "data/seeds/site_gallery.json": b"{}",
            "data/releases/catalog.json": EMPTY_CATALOG,
            "data/cache/current.bin": b"x" * REPOSITORY_SIZE.MAX_APPROVED_DATA_BLOB_BYTES,
            "artifacts/release/payload.bin": b"y" * REPOSITORY_SIZE.MAX_APPROVED_DATA_BLOB_BYTES,
        },
    )
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), 0)

    report = collect_repository_size(repo, policy)

    assert [(item.code, item.path) for item in report.violations] == [
        ("unapproved_large_release_blob", "artifacts/release/payload.bin"),
        ("unapproved_large_release_blob", "data/cache/current.bin"),
    ]


def test_gate_allows_only_expected_small_authoring_and_compact_data(tmp_path: Path) -> None:
    repo = _repository(
        tmp_path,
        {
            "data/README.md": b"readme",
            "data/licenses/NOTICE.txt": b"notice",
            "data/migrations/012_next.sql": b"select 1;",
            "data/seeds/example.json": b"{}",
            "data/releases/catalog.json": EMPTY_CATALOG,
            "data/releases/publication-authority.json": b"{}",
            "data/releases/historical-backfill.json": b"{}",
            "data/optimization_method_selection_database_v0.13.0_manifest.json": b"{}",
        },
    )
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), 0)

    report = collect_repository_size(repo, policy)

    assert report.violations == ()


def test_gate_rejects_small_unapproved_data_path(tmp_path: Path) -> None:
    repo = _repository(tmp_path, {"data/releases/notes.json": b"{}"})
    policy = RepositorySizePolicy(frozenset({"0.12.0"}), 0)

    report = collect_repository_size(repo, policy)

    assert [(item.code, item.path) for item in report.violations] == [
        ("unapproved_data_path", "data/releases/notes.json")
    ]
