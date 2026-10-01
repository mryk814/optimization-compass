"""Report which articles follow their section skeleton (content_skeletons.SKELETONS).

uv run python scripts/content_skeleton_report.py                 # all articles with gaps
uv run python scripts/content_skeleton_report.py --ids bfgs,adam # only these articles
uv run python scripts/content_skeleton_report.py --prune         # drop conforming pending IDs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimization_compass.content_models import load_content
from optimization_compass.content_skeletons import (
    PENDING_PATH,
    SKELETONS,
    load_pending,
    skeleton_gaps,
    skeleton_kind,
)

ROOT = Path(__file__).parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ids", default="", help="comma-separated content IDs")
    parser.add_argument("--prune", action="store_true", help="rewrite the pending list")
    parser.add_argument("--init", action="store_true", help="list every non-conforming article")
    args = parser.parse_args()

    pages = [
        page
        for page in load_content(ROOT / "content")
        if page.status == "published" and skeleton_kind(page) is not None
    ]
    wanted = {item.strip() for item in args.ids.split(",") if item.strip()}
    pending = load_pending(ROOT)
    nonconforming = sorted(page.content_id for page in pages if skeleton_gaps(page))

    if args.init or args.prune:
        keep = nonconforming if args.init else sorted(pending & set(nonconforming))
        (ROOT / PENDING_PATH).write_text(
            json.dumps({"contract_version": "1.0.0", "pending": keep}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"pending: {len(pending)} -> {len(keep)}")
        return

    counts: dict[str, list[int]] = {}
    for page in pages:
        kind = str(skeleton_kind(page))
        gaps = skeleton_gaps(page)
        counts.setdefault(kind, [0, 0])[0 if not gaps else 1] += 1
        if wanted and page.content_id not in wanted:
            continue
        if gaps or wanted:
            state = "ok" if not gaps else ", ".join(gaps)
            flag = " (pending)" if page.content_id in pending else ""
            print(f"{page.content_id} [{kind}]{flag}: {state}")
    for kind, (ok, ng) in sorted(counts.items()):
        print(f"{kind}: {ok} follow / {ng} do not  skeleton = {' → '.join(SKELETONS[kind])}")  # type: ignore[index]


if __name__ == "__main__":
    main()
