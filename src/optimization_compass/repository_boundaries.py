from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

GitRunner = Callable[[Path, tuple[str, ...]], str]


class RepositoryBoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class GitRepositoryBoundaries:
    worktree_roots: tuple[Path, ...]
    common_git_directory: Path


def _run_git(repository_root: Path, arguments: tuple[str, ...]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise RepositoryBoundaryError(
            "cannot establish repository boundaries; refusing external output"
        ) from error
    return result.stdout


def discover_git_repository_boundaries(
    repository_root: Path,
    *,
    runner: GitRunner | None = None,
) -> GitRepositoryBoundaries:
    root = repository_root.resolve(strict=False)
    execute = runner or _run_git
    try:
        worktree_output = execute(root, ("worktree", "list", "--porcelain"))
        common_directory_output = execute(
            root,
            ("rev-parse", "--path-format=absolute", "--git-common-dir"),
        )
    except RepositoryBoundaryError:
        raise
    except Exception as error:
        raise RepositoryBoundaryError(
            "cannot establish repository boundaries; refusing external output"
        ) from error

    worktree_roots = tuple(
        Path(line.removeprefix("worktree ")).resolve(strict=False)
        for line in worktree_output.splitlines()
        if line.startswith("worktree ") and line.removeprefix("worktree ").strip()
    )
    common_directory_lines = [line.strip() for line in common_directory_output.splitlines() if line]
    if (
        not worktree_roots
        or root not in worktree_roots
        or len(common_directory_lines) != 1
        or not Path(common_directory_lines[0]).is_absolute()
    ):
        raise RepositoryBoundaryError(
            "cannot establish repository boundaries; refusing external output"
        )
    return GitRepositoryBoundaries(
        worktree_roots=worktree_roots,
        common_git_directory=Path(common_directory_lines[0]).resolve(strict=False),
    )


def ensure_external_output_path(
    output_path: Path,
    *,
    repository_root: Path,
    runner: GitRunner | None = None,
) -> Path:
    output = output_path.resolve(strict=False)
    boundaries = discover_git_repository_boundaries(repository_root, runner=runner)
    protected_roots = (*boundaries.worktree_roots, boundaries.common_git_directory)
    if any(output == protected or protected in output.parents for protected in protected_roots):
        raise RepositoryBoundaryError("output must be outside every repository worktree")
    return output
