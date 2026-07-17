from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from optimization_compass.dataset_release import (
    TARGET_DATASET_VERSION,
    build_staged_release,
    verify_release_tree,
)

ROOT = Path(__file__).parents[1]
BASE_DATABASE = ROOT / "data/optimization_method_selection_database_v0.2.0.sqlite"
RUNTIME_DATABASE = ROOT / "src/optimization_compass/resources/knowledge.sqlite"


def test_staged_release_bundles_and_validates_license_notices(tmp_path: Path) -> None:
    release = build_staged_release(BASE_DATABASE, tmp_path / "release")
    manifest = json.loads(release.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 2
    assert manifest["licenses"]["code"] == {
        "spdx_id": "MIT",
        "path": "licenses/LICENSE.txt",
    }
    assert manifest["licenses"]["data"]["spdx_id"] == "CC-BY-4.0"
    assert manifest["licenses"]["content"]["spdx_id"] == "CC-BY-4.0"
    for name in ("LICENSE", "DATA_LICENSE", "CONTENT_LICENSE", "CC-BY-4.0", "NOTICE"):
        assert (release.output_directory / "licenses" / f"{name}.txt").read_bytes() == (
            ROOT / name
        ).read_bytes()

    csv_zip = release.output_directory / manifest["artifacts"]["csv_zip"]
    with zipfile.ZipFile(csv_zip) as archive:
        assert archive.namelist()[-3:] == [
            "LICENSES/DATA_LICENSE.txt",
            "LICENSES/CC-BY-4.0.txt",
            "LICENSES/NOTICE.txt",
        ]
        assert archive.read("LICENSES/DATA_LICENSE.txt") == (ROOT / "DATA_LICENSE").read_bytes()

    assert verify_release_tree(release.output_directory).ok is True


def test_site_license_manifest_paths_resolve() -> None:
    public = ROOT / "site/public"
    manifest = json.loads((public / "data/manifest.json").read_text(encoding="utf-8"))

    assert manifest["licenses"]["code"]["spdx_id"] == "MIT"
    assert manifest["licenses"]["data"]["spdx_id"] == "CC-BY-4.0"
    assert manifest["licenses"]["content"]["spdx_id"] == "CC-BY-4.0"
    paths = [
        manifest["licenses"]["code"]["path"],
        manifest["licenses"]["data"]["path"],
        manifest["licenses"]["content"]["path"],
        manifest["licenses"]["legal_code_path"],
        manifest["licenses"]["notice_path"],
    ]
    assert all((public / path).is_file() for path in paths)


def test_source_catalog_uses_retained_runtime_database_for_compact_release() -> None:
    assert RUNTIME_DATABASE.is_file()
    assert not (
        ROOT / f"data/optimization_method_selection_database_v{TARGET_DATASET_VERSION}.sqlite"
    ).exists()

    result = subprocess.run(
        [sys.executable, "scripts/verify_licensing.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "validated license notices" in result.stdout
    assert "source records across" in result.stdout
