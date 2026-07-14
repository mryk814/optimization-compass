from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from optimization_compass.db import KnowledgeRepository
from optimization_compass.source_health import SourceHealthReport, build_source_health_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report source-link and metadata freshness health."
    )
    parser.add_argument("--output", type=Path, default=Path("source-health-report"))
    parser.add_argument("--check-network", action="store_true")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--fail-on-broken", action="store_true")
    args = parser.parse_args()

    report = build_source_health_report(
        KnowledgeRepository(), as_of=args.as_of, check_network=args.check_network
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "report.json").write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output / "report.md").write_text(_markdown(report), encoding="utf-8")
    broken = [link for link in report.links if link.status in {"broken", "tls_error"}]
    print(
        f"source health: {len(report.structural_errors)} structural errors, "
        f"{len(broken)} confirmed broken/TLS links, "
        f"{len(report.stale_candidates)} stale candidates"
    )
    return int(bool(report.structural_errors or (args.fail_on_broken and broken)))


def _markdown(report: SourceHealthReport) -> str:
    broken = [link for link in report.links if link.status in {"broken", "tls_error"}]
    advisory = [
        link for link in report.links if link.status not in {"healthy", "broken", "tls_error"}
    ]
    lines = [
        "# Source health report",
        "",
        f"Generated: {report.generated_on.isoformat()}",
        f"Network checked: {'yes' if report.network_checked else 'no'}",
        "",
        f"- Structural errors: {len(report.structural_errors)}",
        f"- Confirmed broken or TLS errors: {len(broken)}",
        f"- Redirect/rate-limit/transient advisories: {len(advisory)}",
        f"- Stale metadata candidates: {len(report.stale_candidates)}",
        "",
        "Scheduled checks only report findings; they never rewrite authority data.",
        "",
    ]
    for title, items in (
        ("Structural errors", report.structural_errors),
        (
            "Confirmed broken or TLS errors",
            [f"{x.source_id}: {x.status} {x.detail}" for x in broken],
        ),
        ("Advisories", [f"{x.source_id}: {x.status} {x.detail}" for x in advisory]),
        (
            "Stale metadata candidates",
            [
                f"{x.entity_type}:{x.entity_id}: {', '.join(x.stale_fields)} "
                f"({x.age_days}/{x.max_age_days} days)"
                for x in report.stale_candidates
            ],
        ),
    ):
        lines.extend([f"## {title}", ""])
        lines.extend([f"- {item}" for item in items] or ["- None"])
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
