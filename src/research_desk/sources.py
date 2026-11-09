"""Citation store + offline mock search backend with seeded sources."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Source:
    """A verifiable source a claim can cite."""

    id: str
    title: str
    url: str
    text: str


def seeded_sources() -> list[Source]:
    """Built-in source corpus (offline, deterministic)."""
    return [
        Source("s1", "Singapore AI adoption survey 2026", "https://example.org/sg-ai-2026",
               "72 percent of Singapore enterprises piloted AI agents in 2026, up from 48 percent in 2025."),
        Source("s2", "Agent reliability study", "https://example.org/agent-reliability",
               "Multi-agent fact-checking reduced unsupported claims by 61 percent versus single-agent drafting."),
        Source("s3", "Enterprise agent costs", "https://example.org/agent-costs",
               "Median enterprise agent deployment cost fell 38 percent year on year as open models improved."),
        Source("s4", "Human oversight guidance", "https://example.org/oversight",
               "Regulators recommend human approval for consequential agent actions including payments and external sends."),
        Source("s5", "Retrieval grounding paper", "https://example.org/grounding",
               "Retrieval grounding with citations improved answer factuality by 44 percent on research tasks."),
    ]


def _stem(word: str) -> str:
    """Crude singular stem so 'agents' matches 'agent'."""
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def _terms(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())}


class MockSearch:
    """Keyword search over the local source corpus. No network."""

    def __init__(self, sources: list[Source] | None = None) -> None:
        self.sources = sources if sources is not None else seeded_sources()

    def search(self, query: str, k: int = 3) -> list[Source]:
        """Return sources ranked by query-term overlap."""
        q = _terms(query)
        scored = [(len(q & _terms(s.title + " " + s.text)), s) for s in self.sources]
        ranked = sorted([x for x in scored if x[0] > 0], key=lambda x: -x[0])
        return [s for _, s in ranked[:k]]

    def get(self, source_id: str) -> Source | None:
        """Look up a source by id."""
        return next((s for s in self.sources if s.id == source_id), None)

    def verify(self, claim_text: str, source: Source) -> bool:
        """A claim is verified if its key terms are supported by the source.

        Heuristic for the offline build: at least half the claim's content
        terms must appear in the source text.
        """
        claim_terms = _terms(claim_text) - {
            "the", "a", "an", "of", "in", "by", "to", "and", "percent"}
        if not claim_terms:
            return False
        src_terms = _terms(source.text)
        overlap = len(claim_terms & src_terms) / len(claim_terms)
        return overlap >= 0.4
