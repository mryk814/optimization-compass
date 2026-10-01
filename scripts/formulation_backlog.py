"""Rank formulations that still lack an article by how much a learner would meet them (ADR 0017).

The score is a reading-demand estimate from generated data, not a quality judgement:

- 3 points for each learning-path step that already sends readers to the formulation;
- 2 points for each published Gallery case rooted in it;
- 1 point for each relation that connects it to another form.

Run after ``optimization-compass export-site-data``:

    uv run python scripts/formulation_backlog.py --limit 10
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DATA = ROOT / "site/public/data"


def rank_backlog(atlas: dict, paths: dict) -> list[dict]:  # type: ignore[type-arg]
    path_hits: dict[str, list[str]] = {}
    for path in paths["paths"]:
        for step in path["steps"]:
            if step["target_type"] == "formulation":
                path_hits.setdefault(step["target_id"], []).append(path["path_id"])
    degree: dict[str, int] = {}
    for relation in atlas["relations"]:
        for endpoint in (relation["from"], relation["to"]):
            degree[endpoint] = degree.get(endpoint, 0) + 1
    rows = []
    for item in atlas["formulations"]:
        if item["maturity"] != "skeleton":
            continue
        problem_id = item["problem_id"]
        score = (
            3 * len(path_hits.get(problem_id, []))
            + 2 * len(item["cases"])
            + degree.get(problem_id, 0)
        )
        rows.append(
            {
                "problem_id": problem_id,
                "name_ja": item["name_ja"],
                "score": score,
                "paths": path_hits.get(problem_id, []),
                "cases": len(item["cases"]),
                "relations": degree.get(problem_id, 0),
            }
        )
    return sorted(rows, key=lambda row: (-row["score"], row["problem_id"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    atlas = json.loads((DATA / "formulation-atlas.json").read_text(encoding="utf-8"))
    paths = json.loads((DATA / "learning-paths.json").read_text(encoding="utf-8"))
    rows = rank_backlog(atlas, paths)
    summary = atlas["summary"]
    print(f"articles: {summary['with_article']} / {summary['formulations']} formulations")
    print("score  id     name  (paths / cases / relations)")
    for row in rows[: args.limit]:
        print(
            f"{row['score']:>5}  {row['problem_id']}  {row['name_ja']}  "
            f"({','.join(row['paths']) or '-'} / {row['cases']} / {row['relations']})"
        )


if __name__ == "__main__":
    main()
