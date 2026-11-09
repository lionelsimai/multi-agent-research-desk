"""Consensus logic + report generator.

A claim is published only if it passes two *independent* checks:
(1) the FactChecker's content citation-check against the source found via
search (lexical overlap + numeral match + negation parity), and
(2) an existence check in the separate :class:`CitationStore`.
Claims that fail either check are excluded, never published as fact.
A topic with no matching sources yields an empty report — there is no
full-corpus fallback.
"""
from __future__ import annotations

from dataclasses import dataclass

from .agents import Claim, FactChecker, Researcher, Writer
from .sources import CitationStore, MockSearch, Source, seeded_sources


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
        """Fraction of published claims that passed the citation check."""
        if not self.claims:
            return 0.0
        ok = sum(1 for c in self.claims if c.verified and c.source_id)
        return ok / len(self.claims)


def consensus(claim: Claim, fact_checker: FactChecker,
              store: CitationStore) -> bool:
    """Consensus = content citation-check passes AND citation exists.

    The two checks use independent lookups: the FactChecker resolves the
    source through search; existence is resolved through the CitationStore.
    """
    source_exists = store.exists(claim.source_id)
    vote = fact_checker.check(claim)
    claim.verified = bool(source_exists and vote)
    claim.votes["citation_store"] = source_exists
    return claim.verified


class ResearchDesk:
    """Orchestrates Researcher -> FactChecker + CitationStore -> Writer."""

    def __init__(self, search: MockSearch | None = None,
                 store: CitationStore | None = None) -> None:
        self.search = search or MockSearch()
        # Built from a separate construction of the corpus so the existence
        # check does not share the search object's ranking/lookup path.
        self.store = store or CitationStore(seeded_sources())
        self.researcher = Researcher(self.search)
        self.fact_checker = FactChecker(self.search)
        self.writer = Writer()

    def produce(self, topic: str) -> Report:
        """Produce a cited report; only consensus-passing claims publish.

        A topic with no matching sources produces an empty report stating
        that no sources were found (0 claims published).
        """
        result = self.researcher.research(topic)
        published: list[Claim] = []
        rejected: list[Claim] = []
        for claim in result.claims:
            (published if consensus(claim, self.fact_checker, self.store)
             else rejected).append(claim)
        body = self.writer.draft(topic, published)
        if published:
            refs = "\n".join(f"[{s.id}] {s.title} — {s.url}"
                             for s in result.sources
                             if any(c.source_id == s.id for c in published))
            markdown = body + "\n## Sources\n\n" + refs + "\n"
        elif not result.sources:
            markdown = (body + "\nNo sources found for this topic in the "
                        "local corpus; no claims are published.\n")
        else:
            markdown = (body + "\nSources were found, but no claim passed "
                        "the citation check; none are published.\n")
        if rejected:
            markdown += (f"\n<!-- {len(rejected)} claim(s) rejected by consensus "
                         "and excluded from the report -->\n")
        used = [s for s in result.sources
                if any(c.source_id == s.id for c in published)]
        return Report(topic=topic, markdown=markdown, claims=published,
                      rejected=rejected, sources=used)
