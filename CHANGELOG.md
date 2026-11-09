# Changelog

All notable changes to this project will be documented in this file.
Format: Keep a Changelog. Versioning: Semantic Versioning.

## [0.1.1] - 2026-11-09
### Fixed
- Full-corpus fallback removed: before, a topic with no matching sources — including `""` and `"zzzz"` — published 5 claims at 100% coverage. Now such topics publish an empty report stating no sources were found (0 claims; probed in tests and benchmark).
- Citation check is number-aware and negation-aware: every numeral in a claim must appear in its source (a figure-flipped "27 percent" claim against a "72 percent" source now fails) and a negated claim fails against a non-negated source. The checker docstring that claimed "at least half" the terms must match now states the real threshold, 40 percent (0.4).
- Consensus is now two genuinely independent checks: the FactChecker's content check via search, plus existence in a separate `CitationStore` (before, both "checks" resolved through the same `MockSearch.get`).
- Headline honesty: "verified" replaced with "citation-checked (lexical overlap + number match)" in the README, docs and package description — the check is lexical, not semantic verification.
- CLI `--out` is validated (must end in `.md`, exits 2 otherwise) and warns before overwriting; the topic string is escaped before interpolation into the report's markdown heading.

## [0.1.0] - 2026-11-09
### Added
- Initial public release: working offline demo, CLI, tests, benchmarks, CI gate.
- README with architecture diagram, benchmark section and honest limitations.
