from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from optimization_compass.search_index import (
    SearchIndex,
    evaluate_search_benchmark,
    load_benchmark_cases,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Measure deterministic global-search quality and latency."
    )
    parser.add_argument("--index", type=Path, default=Path("site/public/data/search-index.json"))
    parser.add_argument("--queries", type=Path, default=Path("data/seeds/search_benchmark.json"))
    args = parser.parse_args()
    index = SearchIndex.model_validate_json(args.index.read_bytes())
    cases = load_benchmark_cases(args.queries)
    started = time.perf_counter()
    report = evaluate_search_benchmark(index, cases)
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(
        json.dumps(
            {
                "index_bytes": args.index.stat().st_size,
                "query_count": len(cases),
                "total_ms": round(elapsed_ms, 3),
                "mean_ms": round(elapsed_ms / max(len(cases), 1), 3),
                **report["metrics"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
