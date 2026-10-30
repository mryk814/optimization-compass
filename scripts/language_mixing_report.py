"""Report ordinary English words inside Japanese gallery, comparison, and scenario text.

uv run python scripts/language_mixing_report.py                          # counts per surface
uv run python scripts/language_mixing_report.py --ids gallery:EC021      # words by field
uv run python scripts/language_mixing_report.py --prune                  # drop clean pending IDs
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from optimization_compass.language_mixing import (
    PENDING_PATH,
    SURFACES,
    all_hits,
    load_pending,
    pending_document,
)

ROOT = Path(__file__).parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ids", default="", help="comma-separated surface:item IDs")
    parser.add_argument("--prune", action="store_true", help="rewrite the pending list")
    parser.add_argument("--init", action="store_true", help="list every item that has hits")
    args = parser.parse_args()

    hits = all_hits(ROOT)
    pending = load_pending(ROOT)
    mixed = {key for key, item_hits in hits.items() if item_hits}

    if args.init or args.prune:
        keep = mixed if args.init else pending & mixed
        (ROOT / PENDING_PATH).write_text(
            json.dumps(pending_document(keep), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"pending: {len(pending)} -> {len(keep)}")
        return

    wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
    if wanted:
        for key in sorted(wanted):
            surface, _, item_id = key.partition(":")
            item_hits = hits.get((surface, item_id))  # type: ignore[arg-type]
            if item_hits is None:
                print(f"{key}: unknown item")
                continue
            print(f"{key}: {len(item_hits)} words")
            by_field: dict[str, list[str]] = {}
            for hit in item_hits:
                by_field.setdefault(hit.field, []).append(hit.word)
            for field, words in by_field.items():
                print(f"  {field}: {', '.join(words)}")
        return

    for surface in SURFACES:
        surface_items = {
            item_id: item_hits for (s, item_id), item_hits in hits.items() if s == surface
        }
        rows = [(len(item_hits), item_id) for item_id, item_hits in surface_items.items()]
        words = Counter(hit.word for item_hits in surface_items.values() for hit in item_hits)
        mixed_rows = sorted((row for row in rows if row[0]), reverse=True)
        print(
            f"{surface}: {len(mixed_rows)} of {len(rows)} items mix English, "
            f"{sum(words.values())} words; most: "
            + ", ".join(f"{word} {count}" for word, count in words.most_common(8))
        )
        for count, item_id in mixed_rows[:5]:
            print(f"  {item_id}: {count}")


if __name__ == "__main__":
    main()
