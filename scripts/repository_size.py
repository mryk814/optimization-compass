from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath

from optimization_compass.release_identity import ReleaseIdentityError, validate_semantic_version

HISTORICAL_RELEASE_VERSIONS = frozenset(
    {
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
    }
)

# Filled from the Git index on the PR-A baseline. The gate uses blob bytes, not checkout
# line endings, so it is stable across platforms. A later migration may lower this ceiling.
HISTORICAL_RELEASE_DISTRIBUTION_BASELINE_BYTES = 334_703_071

_RELEASE_PATH_PATTERN = re.compile(
    r"^data/optimization_method_selection_database_v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)(?P<suffix>.*)$"
)
_COMPACT_RELEASE_SUFFIXES = frozenset(
    {"_manifest.json", "_release.json", "_report.md", "_schema.sql"}
)
_ARCHIVE_SUFFIXES = frozenset({".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar", ".zst"})
_APPROVED_DATA_FILES = frozenset(
    {
        "data/README.md",
        "data/releases/catalog.json",
        "data/releases/publication-authority.json",
        "data/releases/historical-backfill.json",
    }
)
_APPROVED_AUTHORING_EXTENSIONS = {
    "data/licenses": frozenset({".txt"}),
    "data/migrations": frozenset({".sql"}),
    "data/seeds": frozenset({".json"}),
}
_RELEASE_PATH_MARKERS = frozenset({"archive", "bundle", "distribution", "release"})
MAX_APPROVED_DATA_BLOB_BYTES = 1_048_576


class RepositorySizeError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepositorySizePolicy:
    historical_release_versions: frozenset[str]
    historical_release_distribution_baseline_bytes: int


DEFAULT_POLICY = RepositorySizePolicy(
    historical_release_versions=HISTORICAL_RELEASE_VERSIONS,
    historical_release_distribution_baseline_bytes=(HISTORICAL_RELEASE_DISTRIBUTION_BASELINE_BYTES),
)


@dataclass(frozen=True)
class RepositorySizeViolation:
    code: str
    path: str | None
    detail: str


@dataclass(frozen=True)
class RepositorySizeReport:
    schema_version: int
    tracked_file_count: int
    tracked_working_tree_bytes: int
    tracked_git_blob_bytes: int
    data_tracked_file_count: int
    data_working_tree_bytes: int
    release_distribution_file_count: int
    release_distribution_working_tree_bytes: int
    release_distribution_git_blob_bytes: int
    historical_release_versions: tuple[str, ...]
    violations: tuple[RepositorySizeViolation, ...]

    def as_json_object(self) -> dict[str, object]:
        return asdict(self)


def collect_repository_size(
    repo_root: Path,
    policy: RepositorySizePolicy = DEFAULT_POLICY,
) -> RepositorySizeReport:
    root = repo_root.resolve()
    tracked = _tracked_index_entries(root)
    blob_sizes = _git_blob_sizes(root, {sha for _, sha in tracked})

    tracked_working_tree_bytes = 0
    tracked_git_blob_bytes = 0
    data_file_count = 0
    data_bytes = 0
    release_file_count = 0
    release_working_tree_bytes = 0
    release_git_blob_bytes = 0
    violations: list[RepositorySizeViolation] = []

    for relative_path, blob_sha in tracked:
        absolute_path = root.joinpath(*PurePosixPath(relative_path).parts)
        try:
            working_tree_bytes = absolute_path.stat().st_size
        except OSError as error:
            raise RepositorySizeError(
                f"tracked working-tree path cannot be read: {relative_path}"
            ) from error
        blob_bytes = blob_sizes[blob_sha]
        tracked_working_tree_bytes += working_tree_bytes
        tracked_git_blob_bytes += blob_bytes

        if relative_path == "data" or relative_path.startswith("data/"):
            data_file_count += 1
            data_bytes += working_tree_bytes

        release_version = release_distribution_version(relative_path)
        if release_version is None and _is_disallowed_archive(relative_path):
            release_file_count += 1
            release_working_tree_bytes += working_tree_bytes
            release_git_blob_bytes += blob_bytes
            violations.append(
                RepositorySizeViolation(
                    code="disallowed_tracked_archive",
                    path=relative_path,
                    detail="tracked archives are forbidden outside the grandfathered release set",
                )
            )
            continue
        if release_version is None and _is_large_release_candidate(relative_path, blob_bytes):
            release_file_count += 1
            release_working_tree_bytes += working_tree_bytes
            release_git_blob_bytes += blob_bytes
            violations.append(
                RepositorySizeViolation(
                    code="unapproved_large_release_blob",
                    path=relative_path,
                    detail=(
                        f"unapproved release/data blob is {blob_bytes} bytes; complete bundles "
                        "must be external assets"
                    ),
                )
            )
            continue
        if release_version is None and relative_path.startswith("data/"):
            if not _is_approved_data_path(relative_path):
                violations.append(
                    RepositorySizeViolation(
                        code="unapproved_data_path",
                        path=relative_path,
                        detail=(
                            "data paths must match the source-input or compact-metadata allowlist"
                        ),
                    )
                )
            continue
        if release_version is None:
            continue
        release_file_count += 1
        release_working_tree_bytes += working_tree_bytes
        release_git_blob_bytes += blob_bytes
        if release_version not in policy.historical_release_versions:
            violations.append(
                RepositorySizeViolation(
                    code="new_tracked_release_distribution",
                    path=relative_path,
                    detail=(
                        f"version {release_version} is not in the PR-A historical baseline; "
                        "publish complete bundles as release assets"
                    ),
                )
            )

    if (
        policy.historical_release_distribution_baseline_bytes > 0
        and release_git_blob_bytes > policy.historical_release_distribution_baseline_bytes
    ):
        violations.append(
            RepositorySizeViolation(
                code="historical_release_distribution_growth",
                path=None,
                detail=(
                    f"tracked release distribution blobs total {release_git_blob_bytes} bytes; "
                    "PR-A baseline is "
                    f"{policy.historical_release_distribution_baseline_bytes} bytes"
                ),
            )
        )

    return RepositorySizeReport(
        schema_version=1,
        tracked_file_count=len(tracked),
        tracked_working_tree_bytes=tracked_working_tree_bytes,
        tracked_git_blob_bytes=tracked_git_blob_bytes,
        data_tracked_file_count=data_file_count,
        data_working_tree_bytes=data_bytes,
        release_distribution_file_count=release_file_count,
        release_distribution_working_tree_bytes=release_working_tree_bytes,
        release_distribution_git_blob_bytes=release_git_blob_bytes,
        historical_release_versions=tuple(
            sorted(policy.historical_release_versions, key=_version_key)
        ),
        violations=tuple(sorted(violations, key=lambda item: (item.code, item.path or ""))),
    )


def release_distribution_version(relative_path: str) -> str | None:
    match = _RELEASE_PATH_PATTERN.fullmatch(relative_path)
    if match is None:
        return None
    suffix = match.group("suffix")
    if suffix in _COMPACT_RELEASE_SUFFIXES:
        return None
    if suffix == "" or (not suffix.startswith(".") and not suffix.startswith("_")):
        return None
    version = match.group("version")
    try:
        validate_semantic_version(version)
    except ReleaseIdentityError:
        return None
    return version


def _is_approved_data_path(relative_path: str) -> bool:
    if relative_path in _APPROVED_DATA_FILES:
        return True
    match = _RELEASE_PATH_PATTERN.fullmatch(relative_path)
    if match is not None and match.group("suffix") in _COMPACT_RELEASE_SUFFIXES:
        try:
            validate_semantic_version(match.group("version"))
        except ReleaseIdentityError:
            return False
        return True
    path = PurePosixPath(relative_path)
    parent = path.parent.as_posix()
    return path.suffix.lower() in _APPROVED_AUTHORING_EXTENSIONS.get(parent, frozenset())


def _is_disallowed_archive(relative_path: str) -> bool:
    path = PurePosixPath(relative_path.lower())
    return any(path.name.endswith(suffix) for suffix in _ARCHIVE_SUFFIXES)


def _is_large_release_candidate(relative_path: str, blob_bytes: int) -> bool:
    if blob_bytes < MAX_APPROVED_DATA_BLOB_BYTES:
        return False
    if relative_path.startswith("data/"):
        return True
    lowered_parts = {part.lower() for part in PurePosixPath(relative_path).parts}
    return bool(lowered_parts & _RELEASE_PATH_MARKERS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report tracked checkout and release-distribution sizes reproducibly."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Git worktree root (defaults to this repository).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when a tracked release distribution exceeds the PR-A baseline.",
    )
    args = parser.parse_args()
    report = collect_repository_size(args.repo_root)
    print(json.dumps(report.as_json_object(), ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if args.check and report.violations else 0


def _tracked_index_entries(repo_root: Path) -> list[tuple[str, str]]:
    result = _run_git(repo_root, ["ls-files", "--stage", "-z"])
    entries: list[tuple[str, str]] = []
    for raw_entry in result.stdout.split("\0"):
        if not raw_entry:
            continue
        metadata, separator, path = raw_entry.partition("\t")
        if not separator:
            raise RepositorySizeError("unexpected git ls-files output")
        fields = metadata.split()
        if len(fields) != 3 or fields[2] != "0":
            raise RepositorySizeError("repository index must not contain unresolved entries")
        entries.append((path, fields[1]))
    return sorted(entries)


def _git_blob_sizes(repo_root: Path, object_ids: set[str]) -> dict[str, int]:
    if not object_ids:
        return {}
    result = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "--batch-check=%(objectname) %(objectsize)"],
        input="".join(f"{object_id}\n" for object_id in sorted(object_ids)),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RepositorySizeError(f"git cat-file failed: {result.stderr.strip()}")
    sizes: dict[str, int] = {}
    for line in result.stdout.splitlines():
        object_id, size = line.split()
        sizes[object_id] = int(size)
    missing = object_ids - sizes.keys()
    if missing:
        raise RepositorySizeError("git cat-file did not report every tracked object")
    return sizes


def _run_git(repo_root: Path, arguments: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RepositorySizeError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result


def _version_key(version: str) -> tuple[int, int, int]:
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


if __name__ == "__main__":
    raise SystemExit(main())
