from __future__ import annotations

import argparse
import html
import math
from pathlib import Path

from optimization_compass.learning_slices import generate_topology_field_artifact
from optimization_compass.trace_models import TraceFrame
from optimization_compass.traces import generate_gradient_bundle

ROOT = Path(__file__).parents[1]
DEFAULT_OUTPUT = ROOT / "site" / "public" / "media"
DATASET_VERSION_FILE = ROOT / "src" / "optimization_compass" / "resources" / "DATASET_VERSION"


def read_dataset_version() -> str:
    return DATASET_VERSION_FILE.read_text(encoding="utf-8").splitlines()[0].strip()


def generate_article_figures(dataset_version: str) -> dict[str, bytes]:
    return {
        "gradient-family-execution.svg": _gradient_family_svg(dataset_version).encode("utf-8"),
        "topology-field-execution.svg": _topology_field_svg(dataset_version).encode("utf-8"),
    }


def _gradient_family_svg(dataset_version: str) -> str:
    bundle = generate_gradient_bundle(dataset_version=dataset_version)
    traces = bundle.member_traces
    styles = {
        "gradient_descent": ("Gradient Descent", "#245c42"),
        "momentum": ("Momentum", "#c56b32"),
        "adam": ("Adam", "#456b92"),
    }
    plot_x, plot_y, plot_width, plot_height = 60.0, 120.0, 680.0, 420.0
    x_bounds, y_bounds = (-1.8, 1.6), (-0.2, 1.8)

    def project(point: tuple[float, float] | list[float]) -> tuple[float, float]:
        x, y = point
        return (
            plot_x + (x - x_bounds[0]) / (x_bounds[1] - x_bounds[0]) * plot_width,
            plot_y + plot_height - (y - y_bounds[0]) / (y_bounds[1] - y_bounds[0]) * plot_height,
        )

    elements = [
        _svg_open(
            "同じ谷でも、更新則で軌跡が変わる",
            (
                "f(x,y)=100x²+y²を同じ初期点と40回の評価予算で実行した結果です。"
                "Gradient Descent、Momentum、Adamの軌跡と最終目的値を示します。"
            ),
            height=900,
        ),
        '<rect width="800" height="900" rx="24" fill="#f7f6f1"/>',
        '<text x="60" y="54" class="title">同じ谷でも、更新則で軌跡が変わる</text>',
        (
            '<text x="60" y="84" class="subtitle">'
            "f(x,y)=100x²+y² · 同じ初期点 · 40 oracle evaluations · fixed preset"
            "</text>"
        ),
        (
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_width}" height="{plot_height}" '
            'rx="14" fill="#fff" stroke="#cfd8d1"/>'
        ),
    ]
    for level in (1.0, 4.0, 16.0, 64.0, 256.0):
        radius_x, radius_y = math.sqrt(level / 100.0), math.sqrt(level)
        center = project((0.0, 0.0))
        rx = radius_x / (x_bounds[1] - x_bounds[0]) * plot_width
        ry = radius_y / (y_bounds[1] - y_bounds[0]) * plot_height
        elements.append(
            f'<ellipse cx="{center[0]:.2f}" cy="{center[1]:.2f}" rx="{rx:.2f}" '
            f'ry="{ry:.2f}" fill="none" stroke="#d9dfda" stroke-width="1.5"/>'
        )
    optimum = project((0.0, 0.0))
    elements.extend(
        [
            (
                f'<line x1="{optimum[0]:.2f}" y1="{plot_y}" x2="{optimum[0]:.2f}" '
                f'y2="{plot_y + plot_height}" stroke="#e4e8e4"/>'
            ),
            (
                f'<line x1="{plot_x}" y1="{optimum[1]:.2f}" x2="{plot_x + plot_width}" '
                f'y2="{optimum[1]:.2f}" stroke="#e4e8e4"/>'
            ),
            (
                f'<circle cx="{optimum[0]:.2f}" cy="{optimum[1]:.2f}" r="6" '
                'fill="#fff" stroke="#1f2924" stroke-width="2"/>'
            ),
            (
                f'<text x="{optimum[0] + 12:.2f}" y="{optimum[1] - 10:.2f}" '
                'class="axis">optimum</text>'
            ),
        ]
    )
    for trace in traces:
        method = str(trace.frames[0].payload["method"])
        label, color = styles[method]
        points = [
            project(tuple(frame.points[0].coordinates)) for frame in trace.frames if frame.points
        ]
        point_string = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        elements.extend(
            [
                (
                    f'<polyline points="{point_string}" fill="none" stroke="{color}" '
                    'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                ),
                (
                    f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="6" fill="#fff" '
                    f'stroke="{color}" stroke-width="3"/>'
                ),
                f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="7" fill="{color}"/>',
            ]
        )
        terminal_value = _objective_value(trace.frames[-1])
        row_y = 612 + list(styles).index(method) * 72
        elements.extend(
            [
                (
                    f'<line x1="60" y1="{row_y}" x2="100" y2="{row_y}" '
                    f'stroke="{color}" stroke-width="5"/>'
                ),
                f'<text x="116" y="{row_y + 6}" class="method">{html.escape(label)}</text>',
                (
                    f'<text x="414" y="{row_y + 6}" class="metric">'
                    f"final f = {_metric(terminal_value)}</text>"
                ),
                (
                    f'<text x="740" y="{row_y + 6}" text-anchor="end" class="status">'
                    f"{html.escape(trace.terminal_status)} · "
                    f"{trace.frames[-1].oracle_evaluations} evals"
                    "</text>"
                ),
            ]
        )
    elements.extend(
        [
            '<text x="60" y="570" class="note">○ start　● terminal　等高線は目的関数値</text>',
            (
                '<text x="60" y="838" class="caption">'
                "実行生成: optimization_compass.traces.generate_gradient_bundle"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="60" y="870" class="caveat">'
                "この固定presetの軌跡であり、一般的な性能rankingではありません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _topology_field_svg(dataset_version: str) -> str:
    artifact = generate_topology_field_artifact(dataset_version)
    primary = next(run for run in artifact.runs if run.role == "primary")
    failure = next(run for run in artifact.runs if run.role == "failure_contrast")
    panels = (
        ("初期field", primary.steps[0]),
        ("filterあり · 反復6", primary.steps[6]),
        ("filterあり · 反復12", primary.steps[12]),
        ("filterなし · 反復12", failure.steps[12]),
    )
    elements = [
        _svg_open(
            "同じ12反復でも、filterの有無でfieldが変わる",
            (
                "8×4要素のトポロジー最適化教育generatorの実行結果です。"
                "初期field、filterありの中間と終端、filterなしの終端を、"
                "compliance、gray fraction、checkerboard scoreとともに示します。"
            ),
            height=1000,
        ),
        '<rect width="800" height="1000" rx="24" fill="#f7f6f1"/>',
        '<text x="36" y="54" class="title">同じ12反復でも、filterの有無でfieldが変わる</text>',
        (
            '<text x="36" y="84" class="subtitle">'
            "8×4 density field · volume target 0.50 · deterministic teaching run"
            "</text>"
        ),
    ]
    panel_width = 350
    panel_height = 360
    cell_size = 36
    grid_width = artifact.grid.columns * cell_size
    for index, (label, step) in enumerate(panels):
        panel_x = 36 + (index % 2) * 378
        panel_y = 116 + (index // 2) * 386
        grid_x = panel_x + (panel_width - grid_width) / 2
        grid_y = panel_y + 54
        accent = "#a33d30" if "filterなし" in label else "#245c42"
        elements.extend(
            [
                (
                    f'<rect x="{panel_x}" y="{panel_y}" width="{panel_width}" '
                    f'height="{panel_height}" rx="16" '
                    'fill="#fff" stroke="#cfd8d1"/>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 34}" class="panel-title" '
                    f'fill="{accent}">{html.escape(label)}</text>'
                ),
            ]
        )
        for cell_index, density in enumerate(step.density):
            x = grid_x + (cell_index % artifact.grid.columns) * cell_size
            y = grid_y + (cell_index // artifact.grid.columns) * cell_size
            fill = _density_color(density)
            elements.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_size}" height="{cell_size}" '
                f'fill="{fill}" stroke="#eef1ed" stroke-width="1"/>'
            )
        elements.extend(
            [
                (f'<text x="{panel_x + 18}" y="{panel_y + 230}" class="metric">compliance</text>'),
                (
                    f'<text x="{panel_x + 332}" y="{panel_y + 230}" text-anchor="end" '
                    f'class="metric-value">{step.compliance:.2f}</text>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 268}" '
                    'class="metric">gray fraction</text>'
                ),
                (
                    f'<text x="{panel_x + 332}" y="{panel_y + 268}" text-anchor="end" '
                    f'class="metric-value">{step.gray_fraction:.3f}</text>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 306}" '
                    'class="metric">checkerboard</text>'
                ),
                (
                    f'<text x="{panel_x + 332}" y="{panel_y + 306}" text-anchor="end" '
                    f'class="metric-value">{step.checkerboard_score:.3f}</text>'
                ),
                (
                    f'<text x="{panel_x + 18}" y="{panel_y + 340}" class="status">'
                    f"iteration {step.iteration} · volume {step.volume_fraction:.3f}</text>"
                ),
                (
                    f'<line x1="{panel_x + 18}" y1="{panel_y + 350}" '
                    f'x2="{panel_x + 332}" y2="{panel_y + 350}" '
                    f'stroke="{accent}" stroke-width="3"/>'
                ),
            ]
        )
    elements.extend(
        [
            (
                '<text x="36" y="912" class="caption">'
                "濃いセルほどdensityが高い。指標はfieldと同じ反復から取得。</text>"
            ),
            (
                '<text x="36" y="944" class="caption">'
                "実行生成: optimization_compass.learning_slices.generate_topology_field_artifact"
                f" · dataset {html.escape(dataset_version)}</text>"
            ),
            (
                '<text x="36" y="976" class="caveat">'
                "8×4の教育用referenceであり、実FEM・強度・座屈・製造性を保証しません。"
                "</text>"
            ),
            _svg_style(),
            "</svg>\n",
        ]
    )
    return "".join(elements)


def _svg_open(title: str, description: str, *, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 {height}" '
        'role="img" aria-labelledby="figure-title figure-description">'
        f'<title id="figure-title">{html.escape(title)}</title>'
        f'<desc id="figure-description">{html.escape(description)}</desc>'
    )


def _svg_style() -> str:
    return (
        "<style>"
        "text{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;fill:#26352d}"
        ".title{font-size:28px;font-weight:750}"
        ".subtitle{font-size:16px;fill:#617068}"
        ".panel-title,.method{font-size:19px;font-weight:750}"
        ".metric,.metric-value{font-size:16px;font-variant-numeric:tabular-nums}"
        ".metric-value{font-weight:750}"
        ".status,.axis,.note{font-size:14px;fill:#617068}"
        ".caption{font-size:15px;fill:#46554d}"
        ".caveat{font-size:14px;fill:#7a4b38}"
        "</style>"
    )


def _objective_value(frame: TraceFrame) -> float:
    return next(float(metric.value) for metric in frame.metrics if metric.metric_id == "objective")


def _metric(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) < 0.001 or abs(value) >= 10_000:
        return f"{value:.2e}"
    return f"{value:.4g}"


def _density_color(value: float) -> str:
    low = (243, 242, 236)
    high = (36, 92, 66)
    ratio = min(1.0, max(0.0, value))
    red, green, blue = (
        round(low[index] + (high[index] - low[index]) * ratio) for index in range(3)
    )
    return f"#{red:02x}{green:02x}{blue:02x}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic executable-result figures embedded in learning articles."
        )
    )
    parser.add_argument("--check", action="store_true", help="Fail when tracked figures are stale.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    dataset_version = read_dataset_version()
    figures = generate_article_figures(dataset_version)
    stale: list[str] = []
    for name, payload in figures.items():
        destination = args.output / name
        if args.check:
            if not destination.is_file() or destination.read_bytes() != payload:
                stale.append(str(destination.relative_to(ROOT)))
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
    if stale:
        raise SystemExit("stale article figures: " + ", ".join(stale))
    if not args.check:
        print(f"generated {len(figures)} article figures for dataset {dataset_version}")


if __name__ == "__main__":
    main()
