from __future__ import annotations

import argparse
import json
from importlib.metadata import Distribution, distributions
from pathlib import Path
from typing import Any


def _python_license(distribution: Distribution) -> str:
    metadata = distribution.metadata
    for field in ("License-Expression", "License"):
        value = metadata.get(field, "").strip()
        if value and value.upper() != "UNKNOWN":
            return value
    prefix = "License ::"
    classifiers = metadata.get_all("Classifier", [])
    licenses = [
        value.removeprefix(prefix).strip() for value in classifiers if value.startswith(prefix)
    ]
    return "; ".join(licenses) or "UNKNOWN"


def python_dependencies(installed: list[Distribution] | None = None) -> list[dict[str, Any]]:
    installed = list(distributions()) if installed is None else installed
    packages = []
    for distribution in installed:
        name = distribution.metadata.get("Name", "").strip()
        if not name:
            continue
        packages.append(
            {
                "name": name,
                "version": distribution.version,
                "license": _python_license(distribution),
            }
        )
    return sorted(packages, key=lambda item: (item["name"].casefold(), item["version"]))


def _node_name(path: str, metadata: dict[str, Any]) -> str:
    declared = metadata.get("name")
    if isinstance(declared, str) and declared:
        return declared
    marker = "node_modules/"
    relative = path.rsplit(marker, maxsplit=1)[-1]
    parts = relative.split("/")
    return "/".join(parts[:2]) if relative.startswith("@") else parts[0]


def node_dependencies(lockfile: Path) -> list[dict[str, Any]]:
    payload = json.loads(lockfile.read_text(encoding="utf-8"))
    packages = payload.get("packages")
    if not isinstance(packages, dict):
        raise ValueError(f"{lockfile} does not contain a packages map")

    result = []
    for path, raw_metadata in packages.items():
        if not path or not isinstance(raw_metadata, dict):
            continue
        version = raw_metadata.get("version")
        if not isinstance(version, str) or not version:
            raise ValueError(f"{lockfile}: {path} does not declare a version")
        license_value = raw_metadata.get("license", "UNKNOWN")
        if not isinstance(license_value, str) or not license_value.strip():
            license_value = "UNKNOWN"
        result.append(
            {
                "name": _node_name(path, raw_metadata),
                "version": version,
                "license": license_value,
                "development": bool(raw_metadata.get("dev", False)),
                "optional": bool(raw_metadata.get("optional", False)),
                "lock_path": path,
            }
        )
    return sorted(
        result, key=lambda item: (item["name"].casefold(), item["version"], item["lock_path"])
    )


def build_report(node_lock: Path) -> dict[str, Any]:
    python = python_dependencies()
    node = node_dependencies(node_lock)
    return {
        "schema_version": 1,
        "python": {"package_count": len(python), "packages": python},
        "node": {"package_count": len(node), "packages": node},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a deterministic dependency license inventory."
    )
    parser.add_argument("--node-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args.node_lock)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {report['python']['package_count']} Python and "
        f"{report['node']['package_count']} npm dependency licenses to {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
