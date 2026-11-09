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


_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_NEGATIONS = {"not", "no", "never", "none", "without", "cannot", "n't"}


def _numbers(text: str) -> list[str]:
    """All numerals in ``text``, in order."""
    return _NUMBER.findall(text)


def _negated(text: str) -> bool:
    """True if ``text`` carries a negation word."""
    words = set(re.findall(r"[a-z']+", text.lower()))
    return bool(words & _NEGATIONS)


def numbers_match(claim_text: str, source_text: str) -> bool:
    """Every numeral in the claim must appear in the source (multiset).

    This is what stops figure-flipping: "fell 83 percent" against a source
    that says "fell 38 percent" fails even though every word overlaps.
    Claims without numerals pass this check vacuously.
    """
    from collections import Counter

    return not (Counter(_numbers(claim_text)) - Counter(_numbers(source_text)))


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
        """Citation-check a claim against its source. All three must hold:

        1. at least 40 percent (threshold 0.4) of the claim's content terms
           appear in the source text (lexical overlap);
        2. every numeral in the claim appears in the source — flipped
           figures fail even when all the words match;
        3. negation parity: a claim that negates (or un-negates) its source
           fails.

        This is a lexical citation check, not semantic verification.
        """
        claim_terms = _terms(claim_text) - {
            "the", "a", "an", "of", "in", "by", "to", "and", "percent"}
        if not claim_terms:
            return False
        src_terms = _terms(source.text)
        overlap = len(claim_terms & src_terms) / len(claim_terms)
        if overlap < 0.4:
            return False
        if not numbers_match(claim_text, source.text):
            return False
        return _negated(claim_text) == _negated(source.text)


class CitationStore:
    """Independent citation registry: source id -> Source.

    Existence checks go through this store — a lookup path built separately
    from :class:`MockSearch`'s ranking — so consensus is two genuinely
    independent checks (content check via search, existence via this
    store), not one lookup counted twice (the pre-0.1.1 design).
    """

    def __init__(self, sources: list[Source]) -> None:
        self._by_id: dict[str, Source] = {s.id: s for s in sources}

    def get(self, source_id: str) -> Source | None:
        """Look up a cited source by id, or None if it does not exist."""
        return self._by_id.get(source_id)

    def exists(self, source_id: str) -> bool:
        """True iff ``source_id`` is registered in the store."""
        return source_id in self._by_id

    def __len__(self) -> int:
        return len(self._by_id)
