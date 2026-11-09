"""Consensus logic + report generator.

A claim is published only if it passes consensus: the FactChecker verifies
it against its source AND the Researcher's grounding is intact (source
exists). Unverified claims are listed separately, never published as fact.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agents import Claim, FactChecker, Researcher, Writer
from .sources import MockSearch, Source


@dataclass
class Report:
    """A finished, cited report."""

    topic: str
    markdown: str
    claims: list[Claim]
    rejected: list[Claim]
    sources: list[Source]

    @property
    def citation_coverage(self) -> float:
        """Fraction of published claims with a verified citation (target 1.0)."""
        if not self.claims:
            return 0.0
        ok = sum(1 for c in self.claims if c.verified and c.source_id)
        return ok / len(self.claims)


def consensus(claim: Claim, fact_checker: FactChecker,
              search: MockSearch) -> bool:
    """Consensus = fact-check vote passes AND the cited source exists."""
    source_exists = search.get(claim.source_id) is not None
    vote = fact_checker.check(claim)
    claim.verified = bool(source_exists and vote)
    claim.votes["grounding"] = source_exists
    return claim.verified


class ResearchDesk:
    """Orchestrates Researcher -> FactChecker (consensus) -> Writer."""

    def __init__(self, search: MockSearch | None = None) -> None:
        self.search = search or MockSearch()
        self.researcher = Researcher(self.search)
        self.fact_checker = FactChecker(self.search)
        self.writer = Writer()

    def produce(self, topic: str) -> Report:
        """Produce a cited report; only consensus-passing claims publish."""
        result = self.researcher.research(topic)
        published: list[Claim] = []
        rejected: list[Claim] = []
        for claim in result.claims:
            (published if consensus(claim, self.fact_checker, self.search)
             else rejected).append(claim)
        body = self.writer.draft(topic, published)
        refs = "\n".join(f"[{s.id}] {s.title} — {s.url}"
                         for s in result.sources
                         if any(c.source_id == s.id for c in published))
        markdown = body + "\n## Sources\n\n" + refs + "\n"
        if rejected:
            markdown += (f"\n<!-- {len(rejected)} claim(s) rejected by consensus "
                         "and excluded from the report -->\n")
        used = [s for s in result.sources
                if any(c.source_id == s.id for c in published)]
        return Report(topic=topic, markdown=markdown, claims=published,
                      rejected=rejected, sources=used)
