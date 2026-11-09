"""Benchmark: % of published claims with verified citations (target 100%).

Run: python benchmarks/bench_citations.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from research_desk import ResearchDesk  # noqa: E402
from research_desk.agents import Claim  # noqa: E402
from research_desk.desk import consensus  # noqa: E402


def main() -> int:
    """Measure citation coverage and confirm consensus rejects fakes."""
    desk = ResearchDesk()
    report = desk.produce("AI agents enterprise research")
    print(f"Published claims: {len(report.claims)}  Rejected: {len(report.rejected)}")
    print(f"Citation coverage (verified): {report.citation_coverage:.0%}")
    fake = Claim(text="Unicorns founded 900 startups in Singapore in 2026",
                 source_id="s1")
    rejected = not consensus(fake, desk.fact_checker, desk.search)
    print(f"Fabricated claim rejected by consensus: {rejected}")
    assert report.citation_coverage == 1.0 and rejected
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
