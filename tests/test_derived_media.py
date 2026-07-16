import struct
from hashlib import sha256
from pathlib import Path

from optimization_compass.derived_media import DerivedMediaManifest, write_static_media
from optimization_compass.trace_models import AlgorithmTrace
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex


def test_static_media_is_deterministic_and_provenance_complete(tmp_path: Path) -> None:
    scenario_index = VisualizationScenarioIndex.model_validate_json(
        Path("site/public/data/visualization-scenarios.json").read_bytes()
    )
    scenario = next(
        item for item in scenario_index.scenarios if item.scenario_id == "SCENARIO_NM_QUADRATIC"
    )
    trace = AlgorithmTrace.model_validate_json(
        Path("site/public/data/traces/nelder-mead-quadratic.json").read_bytes()
    )
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    first = write_static_media(first_dir, scenario=scenario, trace=trace)
    second = write_static_media(second_dir, scenario=scenario, trace=trace)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    entry = first.entries[0]
    assert entry.source_artifact_sha256 == scenario.artifact.payload_sha256
    assert entry.narration_version == scenario.guided_story.story_version
    assert entry.license_spdx_id == "CC-BY-4.0"
    for file in entry.files:
        first_bytes = (first_dir / file.path).read_bytes()
        second_bytes = (second_dir / file.path).read_bytes()
        assert first_bytes == second_bytes
        assert file.bytes == len(first_bytes)
        assert file.sha256 == sha256(first_bytes).hexdigest()
    thumbnail = next(file for file in entry.files if file.media_kind == "thumbnail")
    thumbnail_bytes = (first_dir / thumbnail.path).read_bytes()
    assert thumbnail_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert struct.unpack(">II", thumbnail_bytes[16:24]) == (600, 338)


def test_exported_media_manifest_matches_files() -> None:
    root = Path("site/public/data")
    manifest = DerivedMediaManifest.model_validate_json((root / "media/manifest.json").read_bytes())

    assert manifest.dataset_version == "0.10.0"
    assert {file.media_kind for file in manifest.entries[0].files} == {
        "thumbnail",
        "static_png",
        "static_svg",
    }
    for file in manifest.entries[0].files:
        content = (root / file.path).read_bytes()
        assert file.bytes == len(content)
        assert file.sha256 == sha256(content).hexdigest()
