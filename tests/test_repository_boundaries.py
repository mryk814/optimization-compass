from __future__ import annotations

from pathlib import Path

import pytest

from optimization_compass.repository_boundaries import (
    GitRunner,
    RepositoryBoundaryError,
    ensure_external_output_path,
)


def _runner_for(
    *,
    main: Path,
    current: Path,
    sibling: Path,
    common_git_directory: Path,
) -> GitRunner:
    def run(_repository_root: Path, arguments: tuple[str, ...]) -> str:
        if arguments == ("worktree", "list", "--porcelain"):
            return "".join(
                f"worktree {path}\nHEAD deadbeef\nbranch refs/heads/test\n\n"
                for path in (main, current, sibling)
            )
        if arguments == ("rev-parse", "--path-format=absolute", "--git-common-dir"):
            return f"{common_git_directory}\n"
        raise AssertionError(arguments)

    return run


@pytest.fixture
def repository_layout(tmp_path: Path) -> tuple[Path, Path, Path, Path, GitRunner]:
    main = tmp_path / "main"
    current = tmp_path / "current"
    sibling = tmp_path / "sibling"
    common_git_directory = tmp_path / "common-git-directory"
    for path in (current, sibling, common_git_directory):
        path.mkdir(parents=True)
    return (
        main,
        current,
        sibling,
        common_git_directory,
        _runner_for(
            main=main,
            current=current,
            sibling=sibling,
            common_git_directory=common_git_directory,
        ),
    )


@pytest.mark.parametrize("protected_index", [0, 1, 2, 3])
def test_rejects_all_git_managed_roots(
    repository_layout: tuple[Path, Path, Path, Path, GitRunner],
    protected_index: int,
) -> None:
    main, current, sibling, common_git_directory, runner = repository_layout
    protected_roots = (main, current, sibling, common_git_directory)

    with pytest.raises(RepositoryBoundaryError, match="outside every repository worktree"):
        ensure_external_output_path(
            protected_roots[protected_index] / "publication",
            repository_root=current,
            runner=runner,
        )


def test_allows_a_true_external_directory(
    repository_layout: tuple[Path, Path, Path, Path, GitRunner],
    tmp_path: Path,
) -> None:
    _main, current, _sibling, _common_git_directory, runner = repository_layout
    external = tmp_path / "external" / "publication"

    assert ensure_external_output_path(
        external,
        repository_root=current,
        runner=runner,
    ) == external.resolve(strict=False)


def test_resolves_symlinked_output_before_checking_boundaries(
    repository_layout: tuple[Path, Path, Path, Path, GitRunner],
    tmp_path: Path,
) -> None:
    main, current, _sibling, _common_git_directory, runner = repository_layout
    alias = tmp_path / "main-alias"
    try:
        alias.symlink_to(main, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks are unavailable: {error}")

    with pytest.raises(RepositoryBoundaryError, match="outside every repository worktree"):
        ensure_external_output_path(
            alias / "publication",
            repository_root=current,
            runner=runner,
        )


def test_git_detection_failure_is_fail_closed(tmp_path: Path) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    def failing_runner(_repository_root: Path, _arguments: tuple[str, ...]) -> str:
        raise OSError("git is unavailable")

    with pytest.raises(RepositoryBoundaryError, match="refusing external output"):
        ensure_external_output_path(
            tmp_path / "external",
            repository_root=repository_root,
            runner=failing_runner,
        )


def test_malformed_git_output_is_fail_closed(tmp_path: Path) -> None:
    repository_root = tmp_path / "repository"
    repository_root.mkdir()

    def malformed_runner(_repository_root: Path, arguments: tuple[str, ...]) -> str:
        if arguments[0] == "worktree":
            return ""
        return "relative-git-directory\n"

    with pytest.raises(RepositoryBoundaryError, match="refusing external output"):
        ensure_external_output_path(
            tmp_path / "external",
            repository_root=repository_root,
            runner=malformed_runner,
        )
