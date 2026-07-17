from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def patch_site_export() -> None:
    path = ROOT / "src/optimization_compass/site_export.py"
    text = path.read_text(encoding="utf-8")
    import_line = (
        "from optimization_compass.failure_discovery import "
        "build_failure_discovery_from_sources\n"
    )
    if import_line not in text:
        anchor = "from optimization_compass.evidence import build_source_evidence_index\n"
        if anchor not in text:
            raise RuntimeError("site_export import anchor changed")
        text = text.replace(anchor, anchor + import_line, 1)

    call = (
        "    _write_json(\n"
        "        output_dir / \"failure-discovery.json\",\n"
        "        build_failure_discovery_from_sources(\n"
        "            dataset_version=release[\"version\"],\n"
        "            gallery_seed=GALLERY_SEED,\n"
        "        ),\n"
        "    )\n"
    )
    if call not in text:
        anchor = "    return manifest\n"
        if anchor not in text:
            raise RuntimeError("site_export return anchor changed")
        text = text.replace(anchor, call + anchor, 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_app() -> None:
    path = ROOT / "site/src/App.tsx"
    text = path.read_text(encoding="utf-8")
    old_import = 'import { FailureModePage } from "./features/failures/FailureModePage";'
    new_import = (
        'import { FailureDiscoveryPage } from '
        '"./features/failures/FailureDiscoveryPage";'
    )
    if new_import not in text:
        if old_import not in text:
            raise RuntimeError("App failure page import anchor changed")
        text = text.replace(old_import, new_import, 1)

    old_route = '<Route path="/failures" element={<FailureModePage />} />'
    new_route = '<Route path="/failures" element={<FailureDiscoveryPage />} />'
    if new_route not in text:
        if old_route not in text:
            raise RuntimeError("App failure route anchor changed")
        text = text.replace(old_route, new_route, 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    patch_site_export()
    patch_app()


if __name__ == "__main__":
    main()
