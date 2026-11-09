"""Benchmark: % of published claims passing the citation check (target 100%).

Also probes the 0.1.1 hardening: a fabricated claim, a figure-flipped claim
and a no-source topic must all be rejected / publish nothing.

Run: python benchmarks/bench_citations.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from research_desk import ResearchDesk  # noqa: E402
from research_desk.agents import Claim  # noqa: E402
from research_desk.desk import consensus  # noqa: E402


def main() -> int:
    """Measure citation coverage and confirm consensus rejects bad claims."""
    desk = ResearchDesk()
    report = desk.produce("AI agents enterprise research")
    print(f"Published claims: {len(report.claims)}  Rejected: {len(report.rejected)}")
    print(f"Citation coverage (citation-checked): {report.citation_coverage:.0%}")
    fake = Claim(text="Unicorns founded 900 startups in Singapore in 2026",
                 source_id="s1")
    rejected = not consensus(fake, desk.fact_checker, desk.store)
    print(f"Fabricated claim rejected by consensus: {rejected}")
    flipped = Claim(text="27 percent of Singapore enterprises piloted AI "
                         "agents in 2026", source_id="s1")
    flipped_rejected = not consensus(flipped, desk.fact_checker, desk.store)
    print(f"Figure-flipped claim (72 -> 27) rejected: {flipped_rejected}")
    empty = desk.produce("quantum cooking recipes")
    print(f"No-source topic published claims: {len(empty.claims)} (must be 0)")
    assert report.citation_coverage == 1.0 and rejected and flipped_rejected
    assert len(empty.claims) == 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
