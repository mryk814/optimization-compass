import struct
from hashlib import sha256
from pathlib import Path

from optimization_compass.derived_media import DerivedMediaManifest, write_derived_media
from optimization_compass.trace_models import AlgorithmTrace
from optimization_compass.visualization_scenarios import VisualizationScenarioIndex


def test_derived_media_is_deterministic_and_provenance_complete(tmp_path: Path) -> None:
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

    first = write_derived_media(first_dir, scenario=scenario, trace=trace)
    second = write_derived_media(second_dir, scenario=scenario, trace=trace)

    for first_file, second_file in zip(
        first.entries[0].files, second.entries[0].files, strict=True
    ):
        assert first_file.media_kind == second_file.media_kind
        assert first_file.sha256 == second_file.sha256, first_file.media_kind
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    entry = first.entries[0]
    assert entry.source_artifact_sha256 == scenario.artifact.payload_sha256
    assert entry.narration_version == scenario.guided_story.story_version
    assert entry.license_spdx_id == "CC-BY-4.0"
    assert entry.animation_frame_indices[0] == 0
    assert entry.animation_frame_indices[-1] == trace.frames[-1].frame_index
    assert entry.frame_duration_seconds == 0.6
    for file in entry.files:
        first_bytes = (first_dir / file.path).read_bytes()
        second_bytes = (second_dir / file.path).read_bytes()
        assert first_bytes == second_bytes
        assert file.bytes == len(first_bytes)
        assert file.sha256 == sha256(first_bytes).hexdigest()
    for text_asset in (entry.captions, entry.transcript):
        first_bytes = (first_dir / text_asset.path).read_bytes()
        second_bytes = (second_dir / text_asset.path).read_bytes()
        assert first_bytes == second_bytes
        assert text_asset.bytes == len(first_bytes)
        assert text_asset.sha256 == sha256(first_bytes).hexdigest()
    thumbnail = next(file for file in entry.files if file.media_kind == "thumbnail")
    thumbnail_bytes = (first_dir / thumbnail.path).read_bytes()
    assert thumbnail_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    assert struct.unpack(">II", thumbnail_bytes[16:24]) == (600, 338)
    gif = next(file for file in entry.files if file.media_kind == "animated_gif")
    webm = next(file for file in entry.files if file.media_kind == "webm")
    assert (first_dir / gif.path).read_bytes().startswith(b"GIF89a")
    assert (first_dir / webm.path).read_bytes().startswith(b"\x1aE\xdf\xa3")
    assert (first_dir / entry.captions.path).read_text(encoding="utf-8").startswith("WEBVTT")
    assert "frame 1" in (first_dir / entry.transcript.path).read_text(encoding="utf-8")


def test_canonical_animation_is_packaged_with_the_python_distribution() -> None:
    from importlib.resources import files

    media = files("optimization_compass.resources").joinpath("derived_media")
    assert media.joinpath("nelder-mead-quadratic-animation.gif").read_bytes().startswith(b"GIF89a")
    assert (
        media.joinpath("nelder-mead-quadratic-animation.webm")
        .read_bytes()
        .startswith(b"\x1aE\xdf\xa3")
    )


def test_exported_media_manifest_matches_files() -> None:
    root = Path("site/public/data")
    manifest = DerivedMediaManifest.model_validate_json((root / "media/manifest.json").read_bytes())

    assert manifest.dataset_version == "0.11.0"
    assert {file.media_kind for file in manifest.entries[0].files} == {
        "thumbnail",
        "static_png",
        "static_svg",
        "animated_gif",
        "webm",
    }
    for file in manifest.entries[0].files:
        content = (root / file.path).read_bytes()
        assert file.bytes == len(content)
        assert file.sha256 == sha256(content).hexdigest()
    for text_asset in (manifest.entries[0].captions, manifest.entries[0].transcript):
        content = (root / text_asset.path).read_bytes()
        assert text_asset.bytes == len(content)
        assert text_asset.sha256 == sha256(content).hexdigest()
