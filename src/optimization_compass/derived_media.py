from __future__ import annotations

import math
import struct
import zlib
from hashlib import sha256
from html import escape
from pathlib import Path
from typing import Literal

from pydantic import Field

from optimization_compass.trace_models import AlgorithmTrace, TraceModel
from optimization_compass.visualization_scenarios import VisualizationScenario

MEDIA_ATTRIBUTION = (
    "Optimization Compass, Copyright 2026 TAKUYA OTANI and Optimization Compass contributors"
)
MediaKind = Literal["thumbnail", "static_png", "static_svg", "animated_gif", "webm"]
MediaType = Literal["image/png", "image/svg+xml", "image/gif", "video/webm"]


class DerivedMediaFile(TraceModel):
    media_kind: MediaKind
    media_type: MediaType
    path: str = Field(pattern=r"^media/[a-z0-9._/-]+\.(png|svg|gif|webm)$")
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    frame_index: int = Field(ge=0)
    duration_seconds: float | None = Field(default=None, gt=0)
    bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DerivedMediaEntry(TraceModel):
    media_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]+$")
    scenario_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    artifact_contract: str = Field(min_length=1)
    artifact_contract_version: str = Field(min_length=1)
    renderer_family: str = Field(min_length=1)
    renderer_contract_version: str = Field(min_length=1)
    source_artifact_path: str = Field(min_length=1)
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    frame_index: int = Field(ge=0)
    viewport_preset: str = Field(min_length=1)
    camera_preset: str | None
    narration_version: str | None
    source_ids: list[str] = Field(min_length=1)
    limitations_ja: str = Field(min_length=1)
    limitations_en: str = Field(min_length=1)
    alt_ja: str = Field(min_length=1)
    alt_en: str = Field(min_length=1)
    caption_ja: str = Field(min_length=1)
    caption_en: str = Field(min_length=1)
    license_spdx_id: Literal["CC-BY-4.0"]
    attribution: str = Field(min_length=1)
    files: list[DerivedMediaFile] = Field(min_length=1)


class DerivedMediaManifest(TraceModel):
    contract_version: Literal["1.0.0"]
    dataset_version: str = Field(min_length=1)
    entries: list[DerivedMediaEntry] = Field(min_length=1)


def write_static_media(
    output_dir: Path,
    *,
    scenario: VisualizationScenario,
    trace: AlgorithmTrace,
) -> DerivedMediaManifest:
    if scenario.scenario_id != "SCENARIO_NM_QUADRATIC":
        raise ValueError("the static-media pilot requires SCENARIO_NM_QUADRATIC")
    if scenario.guided_story is None:
        raise ValueError("the static-media pilot requires an authored guided story")
    if trace.scenario_id != scenario.scenario_id:
        raise ValueError("derived-media trace and scenario identities differ")

    terminal_step = scenario.guided_story.steps[-1]
    frame_index = terminal_step.frame_index
    if frame_index >= len(trace.frames):
        raise ValueError("guided terminal frame is outside the trace")
    bounds = _plot_bounds(trace)
    trajectory = _best_trajectory(trace)
    simplex = [
        point.coordinates
        for point in trace.frames[frame_index].points
        if point.role == "simplex-vertex"
    ]
    if len(simplex) != 3:
        raise ValueError("Nelder-Mead static media requires three terminal simplex vertices")

    slug = scenario.scenario_id.lower().replace("_", "-")
    directory = output_dir / "media" / slug
    directory.mkdir(parents=True, exist_ok=True)
    svg_bytes = _render_svg(scenario, bounds, trajectory, simplex)
    png_bytes = _render_png(1200, 675, bounds, trajectory, simplex)
    thumbnail_bytes = _render_png(600, 338, bounds, trajectory, simplex)
    assets: list[tuple[MediaKind, MediaType, str, bytes, int, int]] = [
        ("static_svg", "image/svg+xml", f"media/{slug}/static.svg", svg_bytes, 1200, 675),
        ("static_png", "image/png", f"media/{slug}/static.png", png_bytes, 1200, 675),
        ("thumbnail", "image/png", f"media/{slug}/thumbnail.png", thumbnail_bytes, 600, 338),
    ]
    files: list[DerivedMediaFile] = []
    for media_kind, media_type, relative_path, content, width, height in assets:
        path = output_dir / relative_path
        path.write_bytes(content)
        files.append(
            DerivedMediaFile(
                media_kind=media_kind,
                media_type=media_type,
                path=relative_path,
                width=width,
                height=height,
                frame_index=frame_index,
                bytes=len(content),
                sha256=sha256(content).hexdigest(),
            )
        )
    entry = DerivedMediaEntry(
        media_id="nelder-mead-quadratic-static",
        scenario_id=scenario.scenario_id,
        dataset_version=scenario.dataset_version,
        artifact_contract=scenario.artifact.artifact_contract,
        artifact_contract_version=scenario.artifact.artifact_contract_version,
        renderer_family=scenario.artifact.renderer_family,
        renderer_contract_version=scenario.artifact.renderer_contract_version,
        source_artifact_path=scenario.artifact.payload_path,
        source_artifact_sha256=scenario.artifact.payload_sha256,
        frame_index=frame_index,
        viewport_preset=terminal_step.viewport_preset,
        camera_preset=terminal_step.camera_preset,
        narration_version=scenario.guided_story.story_version,
        source_ids=scenario.source_ids,
        limitations_ja=scenario.lesson.limitations_ja,
        limitations_en=scenario.lesson.limitations_en,
        alt_ja=scenario.lesson.text_alternative.ja,
        alt_en=scenario.lesson.text_alternative.en,
        caption_ja=scenario.lesson.derived_media_caption.ja,
        caption_en=scenario.lesson.derived_media_caption.en,
        license_spdx_id="CC-BY-4.0",
        attribution=MEDIA_ATTRIBUTION,
        files=files,
    )
    return DerivedMediaManifest(
        contract_version="1.0.0",
        dataset_version=scenario.dataset_version,
        entries=[entry],
    )


def _plot_bounds(trace: AlgorithmTrace) -> tuple[float, float, float, float]:
    display_range = trace.objective.get("display_range")
    if not isinstance(display_range, dict):
        raise ValueError("trace objective has no display range")
    x_min, x_max = _range_pair(display_range.get("x"))
    y_min, y_max = _range_pair(display_range.get("y"))
    return x_min, x_max, y_min, y_max


def _range_pair(value: object) -> tuple[float, float]:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(not isinstance(item, (int, float)) or isinstance(item, bool) for item in value)
    ):
        raise ValueError("trace objective display range is invalid")
    return float(value[0]), float(value[1])


def _best_trajectory(trace: AlgorithmTrace) -> list[list[float]]:
    trajectory: list[list[float]] = []
    for frame in trace.frames:
        vertices = [
            point
            for point in frame.points
            if point.role == "simplex-vertex" and point.value is not None
        ]
        if vertices:
            trajectory.append(min(vertices, key=lambda point: point.value or 0.0).coordinates)
    if len(trajectory) < 2:
        raise ValueError("static media requires a trajectory with at least two points")
    return trajectory


def _render_svg(
    scenario: VisualizationScenario,
    bounds: tuple[float, float, float, float],
    trajectory: list[list[float]],
    simplex: list[list[float]],
) -> bytes:
    mapped_path = " ".join(_svg_point(point, bounds) for point in trajectory)
    mapped_simplex = " ".join(_svg_point(point, bounds) for point in simplex)
    contours = "\n".join(
        f'<ellipse cx="440" cy="355" rx="{radius * 0.34:.1f}" ry="{radius:.1f}" />'
        for radius in (65, 115, 170, 230, 290)
    )
    title = escape(scenario.title_ja)
    summary = escape(scenario.lesson.static_summary.ja)
    limitation = escape(scenario.lesson.limitations_ja)
    font = 'font-family="sans-serif"'
    svg = "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" '
            'viewBox="0 0 1200 675" role="img" aria-labelledby="title description">',
            f'<title id="title">{title}</title>',
            f'<desc id="description">{escape(scenario.lesson.text_alternative.ja)}</desc>',
            '<rect width="1200" height="675" fill="#f4f3ed"/>',
            '<rect x="36" y="32" width="1128" height="611" rx="24" '
            'fill="#ffffff" stroke="#c9d4cc"/>',
            f'<text x="72" y="82" fill="#245c42" {font} font-size="18" '
            'font-weight="700">OPTIMIZATION ATLAS · GUIDED MEDIA</text>',
            f'<text x="72" y="126" fill="#17211b" {font} font-size="34" '
            f'font-weight="800">{title}</text>',
            '<rect x="72" y="146" width="742" height="434" rx="16" '
            'fill="#f1f5f0" stroke="#d4ddd6"/>',
            f'<g fill="none" stroke="#b9c9bd" stroke-width="2">{contours}</g>',
            f'<polyline points="{mapped_path}" fill="none" stroke="#9a462b" '
            'stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>',
            f'<polygon points="{mapped_simplex}" fill="#9fc2ad" fill-opacity="0.55" '
            'stroke="#245c42" stroke-width="5"/>',
            '<g stroke="#245c42" stroke-width="5"><line x1="428" x2="452" '
            'y1="355" y2="355"/><line x1="440" x2="440" y1="343" y2="367"/></g>',
            '<rect x="846" y="146" width="286" height="434" rx="16" fill="#eef4ef"/>',
            f'<text x="874" y="190" fill="#245c42" {font} font-size="16" '
            'font-weight="700">TERMINAL FRAME</text>',
            f'<text x="874" y="228" fill="#17211b" {font} font-size="21" '
            'font-weight="700">simplex + trajectory</text>',
            f'<text x="874" y="280" fill="#3c4c43" {font} font-size="16">{summary[:24]}</text>',
            f'<text x="874" y="312" fill="#3c4c43" {font} font-size="16">{summary[24:48]}</text>',
            f'<text x="874" y="504" fill="#617067" {font} font-size="13">{limitation[:31]}</text>',
            f'<text x="874" y="530" fill="#617067" {font} font-size="13">'
            f"{limitation[31:62]}</text>",
            f'<text x="72" y="618" fill="#617067" {font} font-size="14">Scenario '
            f"{escape(scenario.scenario_id)} · Dataset {escape(scenario.dataset_version)} · "
            "CC BY 4.0</text>",
            "</svg>",
            "",
        ]
    )
    return svg.encode("utf-8")


def _svg_point(point: list[float], bounds: tuple[float, float, float, float]) -> str:
    x = _map(point[0], bounds[0], bounds[1], 90, 790)
    y = _map(point[1], bounds[2], bounds[3], 560, 150)
    return f"{x:.2f},{y:.2f}"


def _render_png(
    width: int,
    height: int,
    bounds: tuple[float, float, float, float],
    trajectory: list[list[float]],
    simplex: list[list[float]],
) -> bytes:
    canvas = _Raster(width, height, (244, 243, 237))
    margin = max(18, round(width * 0.06))
    top = max(42, round(height * 0.22))
    right = width - margin
    bottom = height - margin
    canvas.rectangle(margin, margin, right, bottom, (255, 255, 255))
    plot_right = round(width * 0.72)
    canvas.rectangle(margin + 12, top, plot_right, bottom - 12, (241, 245, 240))
    cx = (margin + 12 + plot_right) // 2
    cy = (top + bottom - 12) // 2
    for radius in (0.12, 0.21, 0.31, 0.41):
        canvas.ellipse(
            cx, cy, round(width * radius * 0.35), round(height * radius), (185, 201, 189)
        )
    mapped = [
        (
            round(_map(point[0], bounds[0], bounds[1], margin + 20, plot_right - 10)),
            round(_map(point[1], bounds[2], bounds[3], bottom - 22, top + 10)),
        )
        for point in trajectory
    ]
    canvas.polyline(mapped, (154, 70, 43), max(2, round(width / 240)))
    vertices = [
        (
            round(_map(point[0], bounds[0], bounds[1], margin + 20, plot_right - 10)),
            round(_map(point[1], bounds[2], bounds[3], bottom - 22, top + 10)),
        )
        for point in simplex
    ]
    canvas.polyline([*vertices, vertices[0]], (36, 92, 66), max(2, round(width / 200)))
    for x, y in vertices:
        canvas.circle(x, y, max(4, round(width / 120)), (36, 92, 66))
    accent_x = round(width * 0.76)
    canvas.rectangle(accent_x, top, right - 12, bottom - 12, (238, 244, 239))
    canvas.rectangle(accent_x + 18, top + 24, right - 34, top + 34, (36, 92, 66))
    canvas.rectangle(accent_x + 18, top + 50, right - 58, top + 58, (107, 131, 116))
    canvas.rectangle(accent_x + 18, bottom - 54, right - 42, bottom - 48, (154, 70, 43))
    return canvas.png_bytes()


def _map(value: float, minimum: float, maximum: float, start: float, end: float) -> float:
    return start + ((value - minimum) / (maximum - minimum)) * (end - start)


class _Raster:
    def __init__(self, width: int, height: int, background: tuple[int, int, int]) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background * (width * height))

    def set(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        offset = (y * self.width + x) * 3
        self.pixels[offset : offset + 3] = bytes(color)

    def rectangle(
        self, left: int, top: int, right: int, bottom: int, color: tuple[int, int, int]
    ) -> None:
        for y in range(max(0, top), min(self.height, bottom)):
            offset = (y * self.width + max(0, left)) * 3
            length = max(0, min(self.width, right) - max(0, left))
            self.pixels[offset : offset + length * 3] = bytes(color) * length

    def line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color: tuple[int, int, int],
        width: int,
    ) -> None:
        x0, y0 = start
        x1, y1 = end
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        error = dx + dy
        while True:
            self.circle(x0, y0, max(1, width // 2), color)
            if x0 == x1 and y0 == y1:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy
                x0 += sx
            if twice <= dx:
                error += dx
                y0 += sy

    def polyline(
        self, points: list[tuple[int, int]], color: tuple[int, int, int], width: int
    ) -> None:
        for start, end in zip(points, points[1:], strict=False):
            self.line(start, end, color, width)

    def circle(self, cx: int, cy: int, radius: int, color: tuple[int, int, int]) -> None:
        for y in range(cy - radius, cy + radius + 1):
            span = round(math.sqrt(max(0, radius * radius - (y - cy) ** 2)))
            for x in range(cx - span, cx + span + 1):
                self.set(x, y, color)

    def ellipse(
        self, cx: int, cy: int, radius_x: int, radius_y: int, color: tuple[int, int, int]
    ) -> None:
        previous: tuple[int, int] | None = None
        for degree in range(0, 361, 2):
            radians = math.radians(degree)
            point = (
                round(cx + radius_x * math.cos(radians)),
                round(cy + radius_y * math.sin(radians)),
            )
            if previous is not None:
                self.line(previous, point, color, 1)
            previous = point

    def png_bytes(self) -> bytes:
        raw = b"".join(
            b"\x00" + bytes(self.pixels[row * self.width * 3 : (row + 1) * self.width * 3])
            for row in range(self.height)
        )
        return b"\x89PNG\r\n\x1a\n" + b"".join(
            (
                _png_chunk(
                    b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0)
                ),
                _png_chunk(b"IDAT", zlib.compress(raw, level=9)),
                _png_chunk(b"IEND", b""),
            )
        )


def _png_chunk(kind: bytes, content: bytes) -> bytes:
    checksum = zlib.crc32(kind + content) & 0xFFFFFFFF
    return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", checksum)
