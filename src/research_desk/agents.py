"""Three agent roles with explicit, testable responsibilities."""
from __future__ import annotations

from dataclasses import dataclass, field

from .sources import MockSearch, Source


@dataclass
class Claim:
    """A single factual claim with its citation and verification state."""

    text: str
    source_id: str
    verified: bool = False
    votes: dict[str, bool] = field(default_factory=dict)


@dataclass
class ResearchResult:
    """Researcher's output: candidate claims grounded in sources."""

    topic: str
    claims: list[Claim]
    sources: list[Source]


# Claim templates per source: (claim text) — kept close to source wording so
# verification is meaningful, not rubber-stamping.
_CLAIM_BY_SOURCE: dict[str, str] = {
    "s1": "72 percent of Singapore enterprises piloted AI agents in 2026",
    "s2": "Multi-agent fact-checking reduced unsupported claims by 61 percent",
    "s3": "Median enterprise agent deployment cost fell 38 percent year on year",
    "s4": "Regulators recommend human approval for consequential agent actions",
    "s5": "Retrieval grounding with citations improved answer factuality by 44 percent",
}


class Researcher:
    """Searches sources and drafts grounded candidate claims."""

    def __init__(self, search: MockSearch) -> None:
        self.search = search

    def research(self, topic: str) -> ResearchResult:
        """Find sources for a topic and draft one claim per source."""
        sources = self.search.search(topic, k=5)
        if not sources:  # fall back to the full corpus for broad topics
            sources = list(self.search.sources)
        claims = [Claim(text=_CLAIM_BY_SOURCE[s.id], source_id=s.id)
                  for s in sources if s.id in _CLAIM_BY_SOURCE]
        return ResearchResult(topic=topic, claims=claims, sources=sources)


class FactChecker:
    """Verifies each claim against its cited source (independent vote)."""

    def __init__(self, search: MockSearch) -> None:
        self.search = search

    def check(self, claim: Claim) -> bool:
        """Vote True only if the cited source supports the claim."""
        source = self.search.get(claim.source_id)
        ok = bool(source) and self.search.verify(claim.text, source)  # type: ignore[arg-type]
        claim.votes["fact_checker"] = ok
        return ok


class Writer:
    """Drafts report prose from verified claims only."""

    def draft(self, topic: str, claims: list[Claim]) -> str:
        """Render verified claims as cited bullet prose."""
        lines = [f"# Research Report: {topic}", ""]
        for c in claims:
            lines.append(f"- {c.text} [{c.source_id}].")
        return "\n".join(lines) + "\n"
