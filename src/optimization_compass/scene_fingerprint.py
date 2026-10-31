"""Fingerprint of what a physical scene's numbers depend on.

A rendered scene must belong to the checked-in model and its numerical environment. The
environment is the locked numpy and scipy versions, not the whole lockfile, so an unrelated
dependency bump (a certificate bundle, a web framework) does not force a regeneration.
"""

from __future__ import annotations

import hashlib
import tomllib
from pathlib import Path

# The scene modules import only these for computation.
NUMERICAL_PACKAGES = ("numpy", "scipy")


def numerical_environment(lock_path: Path) -> str:
    """Locked versions of the packages the scene computations import, as `name==version` lines."""
    lock = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    versions: dict[str, list[str]] = {}
    for package in lock.get("package", []):
        versions.setdefault(package["name"], []).append(package["version"])
    for name in NUMERICAL_PACKAGES:
        if len(versions.get(name, [])) != 1:
            raise ValueError(
                f"{lock_path} must lock exactly one {name}, found {versions.get(name, [])}"
            )
    return "".join(f"{name}=={versions[name][0]}\n" for name in NUMERICAL_PACKAGES)


def generator_input_sha256(root: Path, module: Path, generator: Path) -> str:
    """Hash of the scene module, its generator script, and the numerical environment."""
    parts = (
        module.read_text(encoding="utf-8"),
        generator.read_text(encoding="utf-8"),
        numerical_environment(root / "uv.lock"),
    )
    return hashlib.sha256("".join(parts).encode("utf-8")).hexdigest()
