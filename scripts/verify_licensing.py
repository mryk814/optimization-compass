from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from optimization_compass.dataset_release import TARGET_DATASET_VERSION

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT_FILES = ("LICENSE", "DATA_LICENSE", "CONTENT_LICENSE", "CC-BY-4.0", "NOTICE")
REQUIRED_SOURCE_FIELDS = (
    "source_id",
    "source_type",
    "title",
    "author_or_organization",
    "url",
    "supported_claim",
    "source_quality",
    "currentness_status",
)
EXPECTED_SITE_LICENSES = {
    "code": {"spdx_id": "MIT", "path": "licenses/LICENSE.txt"},
    "data": {"spdx_id": "CC-BY-4.0", "path": "licenses/DATA_LICENSE.txt"},
    "content": {"spdx_id": "CC-BY-4.0", "path": "licenses/CONTENT_LICENSE.txt"},
    "legal_code_path": "licenses/CC-BY-4.0.txt",
    "notice_path": "licenses/NOTICE.txt",
}


def main() -> None:
    _verify_root_notices()
    _verify_documentation_links()
    _verify_site_distribution()
    source_count, source_types = _verify_source_catalog()
    print(
        f"validated license notices, Pages paths, and {source_count} source records "
        f"across {len(source_types)} source types"
    )


def _verify_root_notices() -> None:
    for name in REQUIRED_ROOT_FILES:
        path = ROOT / name
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            raise SystemExit(f"required license notice is missing or empty: {name}")
    if "MIT License" not in (ROOT / "LICENSE").read_text(encoding="utf-8"):
        raise SystemExit("LICENSE does not contain the MIT grant")
    for name in ("DATA_LICENSE", "CONTENT_LICENSE"):
        if "SPDX-License-Identifier: CC-BY-4.0" not in (ROOT / name).read_text(encoding="utf-8"):
            raise SystemExit(f"{name} does not declare CC-BY-4.0")


def _verify_documentation_links() -> None:
    required_mentions = {
        "README.md": REQUIRED_ROOT_FILES + ("THIRD_PARTY_SOURCE_AUDIT.md",),
        "CONTRIBUTING.md": ("Signed-off-by:", "docs/licensing.md", "NOTICE"),
        "docs/licensing.md": REQUIRED_ROOT_FILES + ("THIRD_PARTY_SOURCE_AUDIT.md",),
        "docs/public-release-checklist.md": ("verify_licensing.py", "DATA_LICENSE", "NOTICE"),
    }
    for relative, mentions in required_mentions.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        missing = [mention for mention in mentions if mention not in text]
        if missing:
            raise SystemExit(f"{relative} is missing license references: {', '.join(missing)}")


def _verify_site_distribution() -> None:
    public = ROOT / "site/public"
    manifest = json.loads((public / "data/manifest.json").read_text(encoding="utf-8"))
    licenses = manifest.get("licenses")
    if not isinstance(licenses, dict):
        raise SystemExit("site manifest does not contain license metadata")
    for field, expected in EXPECTED_SITE_LICENSES.items():
        if licenses.get(field) != expected:
            raise SystemExit(f"site manifest license field does not match policy: {field}")
        paths = [expected] if isinstance(expected, str) else [expected["path"]]
        for relative in paths:
            if not (public / relative).is_file():
                raise SystemExit(f"site license path does not resolve: {relative}")
    if not str(licenses.get("attribution", "")).strip():
        raise SystemExit("site manifest attribution is missing")


def _verify_source_catalog() -> tuple[int, set[str]]:
    path = ROOT / f"data/optimization_method_selection_database_v{TARGET_DATASET_VERSION}.sqlite"
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in connection.execute("SELECT * FROM sources ORDER BY source_id")]
    finally:
        connection.close()
    if not rows:
        raise SystemExit("source catalog is empty")
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    source_types: set[str] = set()
    for row in rows:
        missing = [field for field in REQUIRED_SOURCE_FIELDS if not str(row.get(field, "")).strip()]
        if missing:
            raise SystemExit(f"source {row.get('source_id')} is missing: {', '.join(missing)}")
        source_id = row["source_id"]
        url = row["url"]
        if source_id in seen_ids:
            raise SystemExit(f"duplicate source ID: {source_id}")
        if url in seen_urls:
            raise SystemExit(f"duplicate source URL: {url}")
        if not url.startswith("https://"):
            raise SystemExit(f"source URL must use HTTPS: {source_id}")
        seen_ids.add(source_id)
        seen_urls.add(url)
        source_types.add(row["source_type"])
    return len(rows), source_types


if __name__ == "__main__":
    main()
