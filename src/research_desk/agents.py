"""Three agent roles with explicit, testable responsibilities."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .sources import MockSearch, Source


@dataclass
class Claim:
    """A single factual claim with its citation and check state.

    ``verified`` means the claim passed the citation check (lexical
    overlap + numeral match + negation parity against its source) AND the
    independent citation-store existence check. It is a lexical check,
    not semantic verification.
    """

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
        """Find sources for a topic and draft one claim per source.

        No fallback: if search finds no sources, the result is empty and
        the desk publishes an empty report. (Before 0.1.1 a full-corpus
        fallback published claims for *any* topic — including empty and
        nonsense topics.)
        """
        sources = self.search.search(topic, k=5)
        claims = [Claim(text=_CLAIM_BY_SOURCE[s.id], source_id=s.id)
                  for s in sources if s.id in _CLAIM_BY_SOURCE]
        return ResearchResult(topic=topic, claims=claims, sources=sources)


class FactChecker:
    """Citation-checks each claim against its cited source (content vote)."""

    def __init__(self, search: MockSearch) -> None:
        self.search = search

    def check(self, claim: Claim) -> bool:
        """Vote True only if the cited source passes the citation check."""
        source = self.search.get(claim.source_id)
        ok = bool(source) and self.search.verify(claim.text, source)  # type: ignore[arg-type]
        claim.votes["fact_checker"] = ok
        return ok


def _escape_topic(topic: str) -> str:
    """Escape a topic string for safe interpolation into a markdown heading."""
    cleaned = " ".join(topic.split())
    return re.sub(r"([\\#\[\]<>`])", r"\\\1", cleaned)


class Writer:
    """Drafts report prose from citation-checked claims only."""

    def draft(self, topic: str, claims: list[Claim]) -> str:
        """Render citation-checked claims as cited bullet prose."""
        lines = [f"# Research Report: {_escape_topic(topic)}", ""]
        for c in claims:
            lines.append(f"- {c.text} [{c.source_id}].")
        return "\n".join(lines) + "\n"
