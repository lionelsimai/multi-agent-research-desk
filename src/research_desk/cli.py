"""CLI: produce a cited report offline.

  python -m research_desk.cli report --topic "AI agents" --out examples/sample-report.md
  python -m research_desk.cli demo
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .desk import ResearchDesk


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(prog="research-desk")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("--topic", required=True)
    r.add_argument("--out", default="")
    sub.add_parser("demo")
    args = ap.parse_args(argv)
    desk = ResearchDesk()
    topic = args.topic if args.cmd == "report" else "AI agents enterprise"
    report = desk.produce(topic)
    print(report.markdown)
    print(f"Published claims: {len(report.claims)} | Rejected: {len(report.rejected)} "
          f"| Citation coverage: {report.citation_coverage:.0%}")
    if args.cmd == "report" and args.out:
        Path(args.out).write_text(report.markdown, encoding="utf-8")
        print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
