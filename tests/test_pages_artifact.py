from __future__ import annotations

import json
import subprocess
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

COMMIT_SHA = "a" * 40
DATASET_VERSION = "0.3.0"
DATABASE_SHA256 = "b" * 64
ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/pages_artifact.py"
HASH_ROUTES = ("/", "/#/map", "/#/diagnose", "/#/theater/nelder-mead", "/#/gallery", "/#/coverage")
JSON_ASSETS = (
    "data/release.json",
    "data/manifest.json",
    "data/views/problem-structure.json",
    "data/content.json",
    "data/gallery.json",
    "data/comparisons.json",
    "data/traces/index.json",
    "data/coverage.json",
)


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _artifact(root: Path) -> Path:
    artifact = root / "optimization-compass"
    (artifact / "assets").mkdir(parents=True)
    (artifact / "assets/index.js").write_text("export {};", encoding="utf-8")
    (artifact / "assets/index.css").write_text(":root {}", encoding="utf-8")
    (artifact / "index.html").write_text(
        """<!doctype html>
<html><head>
<link rel="icon" href="data:image/svg+xml,<svg></svg>">
<link rel="stylesheet" href="/optimization-compass/assets/index.css">
</head><body><div id="root"></div>
<script type="module" src="/optimization-compass/assets/index.js"></script>
</body></html>
""",
        encoding="utf-8",
    )
    release = {
        "schema_version": 1,
        "dataset_version": DATASET_VERSION,
        "release_date": "2026-07-15",
        "database_sha256": DATABASE_SHA256,
    }
    manifest = {
        "dataset_version": DATASET_VERSION,
        "licenses": {
            "code": {"spdx_id": "MIT", "path": "licenses/LICENSE.txt"},
            "data": {"spdx_id": "CC-BY-4.0", "path": "licenses/DATA_LICENSE.txt"},
            "content": {
                "spdx_id": "CC-BY-4.0",
                "path": "licenses/CONTENT_LICENSE.txt",
            },
            "legal_code_path": "licenses/CC-BY-4.0.txt",
            "notice_path": "licenses/NOTICE.txt",
            "attribution": "Optimization Compass contributors",
        },
    }
    _write_json(artifact / "data/release.json", release)
    _write_json(artifact / "data/manifest.json", manifest)
    for relative in JSON_ASSETS:
        path = artifact / relative
        if path.exists():
            continue
        _write_json(path, {"dataset_version": DATASET_VERSION})
    for name in (
        "LICENSE.txt",
        "DATA_LICENSE.txt",
        "CONTENT_LICENSE.txt",
        "CC-BY-4.0.txt",
        "NOTICE.txt",
    ):
        path = artifact / "licenses" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name, encoding="utf-8")
    return artifact


def _run(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def test_stamp_and_verify_local_artifact_records_deployment_identity(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)

    _run("stamp", "--root", str(artifact), "--commit-sha", COMMIT_SHA)
    result = _run(
        "verify-local",
        "--root",
        str(artifact),
        "--expected-commit-sha",
        COMMIT_SHA,
        "--expected-dataset-version",
        DATASET_VERSION,
    )
    summary = json.loads(result.stdout)

    assert summary["routes"] == list(HASH_ROUTES)
    assert summary["json_assets"] == list(JSON_ASSETS)
    assert summary["dataset_version"] == DATASET_VERSION
    identity = json.loads((artifact / "deployment.json").read_text(encoding="utf-8"))
    assert identity["commit_sha"] == COMMIT_SHA
    assert identity["database_sha256"] == DATABASE_SHA256


def test_verify_local_artifact_rejects_mixed_dataset_versions(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    _run("stamp", "--root", str(artifact), "--commit-sha", COMMIT_SHA)
    _write_json(artifact / "data/gallery.json", {"dataset_version": "9.9.9"})

    result = _run("verify-local", "--root", str(artifact), check=False)

    assert result.returncode == 1
    assert "data/gallery.json" in result.stderr


def test_verify_local_artifact_rejects_identity_that_differs_from_release(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    _run("stamp", "--root", str(artifact), "--commit-sha", COMMIT_SHA)
    identity = json.loads((artifact / "deployment.json").read_text(encoding="utf-8"))
    identity["release_date"] = "2026-07-16"
    _write_json(artifact / "deployment.json", identity)

    result = _run("verify-local", "--root", str(artifact), check=False)

    assert result.returncode == 1
    assert "differs from data/release.json: release_date" in result.stderr


def test_remote_smoke_checks_routes_assets_licenses_and_identity(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    _run("stamp", "--root", str(artifact), "--commit-sha", COMMIT_SHA)
    handler = partial(_QuietHandler, directory=str(artifact.parent))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_port}/optimization-compass/"
        result = _run(
            "smoke-remote",
            "--base-url",
            base_url,
            "--expected-commit-sha",
            COMMIT_SHA,
            "--expected-dataset-version",
            DATASET_VERSION,
            "--attempts",
            "1",
            "--delay-seconds",
            "0",
            "--timeout-seconds",
            "2",
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    summary = json.loads(result.stdout)
    assert summary["commit_sha"] == COMMIT_SHA
    assert summary["routes"] == [base_url.rstrip("/") + route for route in HASH_ROUTES]
    assert summary["json_assets"] == list(JSON_ASSETS)
    assert len(summary["license_paths"]) == 5


def test_remote_smoke_rejects_a_different_commit(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    _run("stamp", "--root", str(artifact), "--commit-sha", COMMIT_SHA)
    handler = partial(_QuietHandler, directory=str(artifact.parent))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = _run(
            "smoke-remote",
            "--base-url",
            f"http://127.0.0.1:{server.server_port}/optimization-compass/",
            "--expected-commit-sha",
            "c" * 40,
            "--expected-dataset-version",
            DATASET_VERSION,
            "--attempts",
            "1",
            "--delay-seconds",
            "0",
            "--timeout-seconds",
            "2",
            check=False,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert result.returncode == 1
    assert "did not converge" in result.stderr
