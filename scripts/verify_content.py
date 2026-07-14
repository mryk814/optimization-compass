import json
from pathlib import Path

from optimization_compass.content_models import load_content


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = load_content(root / "content")
    if len(pages) < 4:
        raise SystemExit("at least four published content pages are required")
    if {page.content_id for page in pages} != {
        "method.nelder-mead",
        "method.gradient-descent",
        "concept.convexity",
        "concept.derivative-free",
    }:
        raise SystemExit("initial content set is incomplete")
    data_root = root / "site" / "public" / "data"
    content_index = json.loads((data_root / "content.json").read_text(encoding="utf-8"))
    gallery_index = json.loads((data_root / "gallery.json").read_text(encoding="utf-8"))
    comparison_index = json.loads((data_root / "comparisons.json").read_text(encoding="utf-8"))
    if content_index.get("dataset_version") != "0.2.0" or len(content_index.get("pages", [])) != 4:
        raise SystemExit("published content index is out of sync")
    if gallery_index.get("dataset_version") != "0.2.0" or len(gallery_index.get("cases", [])) != 4:
        raise SystemExit("problem gallery must contain four cases")
    if comparison_index.get("dataset_version") != "0.2.0" or not comparison_index.get(
        "comparisons"
    ):
        raise SystemExit("comparison index is missing")
    print(f"validated {len(pages)} content pages")


if __name__ == "__main__":
    main()
