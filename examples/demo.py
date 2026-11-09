"""Produce a sample report offline.

Run: python examples/demo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from research_desk import ResearchDesk  # noqa: E402

if __name__ == "__main__":
    report = ResearchDesk().produce("AI agents enterprise")
    print(report.markdown)
    print(f"Coverage: {report.citation_coverage:.0%} "
          f"({len(report.claims)} claims, {len(report.rejected)} rejected)")
