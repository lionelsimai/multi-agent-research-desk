"""Unit + end-to-end tests for the research desk."""
from research_desk.agents import Claim, FactChecker
from research_desk.cli import main
from research_desk.desk import ResearchDesk, consensus
from research_desk.sources import CitationStore, MockSearch, seeded_sources


def test_seeded_sources() -> None:
    srcs = seeded_sources()
    assert len(srcs) == 5 and all(s.url.startswith("https://") for s in srcs)


def test_search_ranks() -> None:
    hits = MockSearch().search("Singapore enterprises AI agents")
    assert hits and hits[0].id == "s1"


def test_verify_rejects_unsupported() -> None:
    search = MockSearch()
    src = search.get("s1")
    assert src is not None
    assert not search.verify("Martians landed in Tuas yesterday morning", src)


def test_fact_checker_vote() -> None:
    desk = ResearchDesk()
    good = desk.researcher.research("AI agents").claims[0]
    assert desk.fact_checker.check(good) is True


def test_consensus_rejects_fake_source() -> None:
    search = MockSearch()
    store = CitationStore(seeded_sources())
    claim = Claim(text="72 percent of Singapore enterprises piloted AI agents in 2026",
                  source_id="nope")
    assert consensus(claim, FactChecker(search), store) is False
    assert claim.verified is False
    assert claim.votes["citation_store"] is False


def test_flipped_figures_fail_citation_check() -> None:
    search = MockSearch()
    src = search.get("s1")
    assert src is not None
    # Same words, flipped figure (72 -> 27): lexical overlap passes, the
    # numeral check must catch it.
    flipped = "27 percent of Singapore enterprises piloted AI agents in 2026"
    assert not search.verify(flipped, src)
    desk = ResearchDesk()
    claim = Claim(text=flipped, source_id="s1")
    assert consensus(claim, desk.fact_checker, desk.store) is False


def test_negated_claim_fails_citation_check() -> None:
    search = MockSearch()
    src = search.get("s4")
    assert src is not None
    negated = ("Regulators do not recommend human approval for "
               "consequential agent actions")
    assert not search.verify(negated, src)


def test_citation_store_is_independent_of_search() -> None:
    desk = ResearchDesk()
    assert desk.store is not desk.search
    assert len(desk.store) == 5 and desk.store.exists("s1")
    assert not desk.store.exists("nope")
    report = desk.produce("AI agents enterprise")
    assert report.claims
    assert all(c.votes.get("citation_store") is True for c in report.claims)
    assert all(c.votes.get("fact_checker") is True for c in report.claims)


def test_report_all_claims_cited_and_verified() -> None:
    report = ResearchDesk().produce("AI agents enterprise")
    assert report.claims, "expected at least one published claim"
    assert report.citation_coverage == 1.0
    assert all(c.verified for c in report.claims)
    assert "## Sources" in report.markdown


def test_report_markdown_cites_sources() -> None:
    report = ResearchDesk().produce("AI agents")
    for claim in report.claims:
        assert f"[{claim.source_id}]" in report.markdown


def test_no_source_topics_publish_zero_claims() -> None:
    desk = ResearchDesk()
    for topic in ("quantum cooking recipes", "", "zzzz"):
        report = desk.produce(topic)
        assert report.claims == [], topic
        assert report.citation_coverage == 0.0
        assert "No sources found" in report.markdown


def test_topic_is_escaped_in_markdown() -> None:
    report = ResearchDesk().produce("AI agents #breaking")
    first_line = report.markdown.splitlines()[0]
    assert first_line == "# Research Report: AI agents \\#breaking"


def test_cli_out_must_be_markdown(tmp_path) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "r.txt"
    assert main(["report", "--topic", "AI agents", "--out", str(out)]) == 2
    assert not out.exists()
    ok = tmp_path / "r.md"
    assert main(["report", "--topic", "AI agents", "--out", str(ok)]) == 0
    assert main(["report", "--topic", "AI agents", "--out", str(ok)]) == 0


def test_cli_demo_e2e(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "Citation coverage: 100%" in out


def test_cli_report_writes_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "r.md"
    assert main(["report", "--topic", "AI agents", "--out", str(out)]) == 0
    assert out.exists() and "Sources" in out.read_text(encoding="utf-8")


def test_config_from_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from research_desk.config import Settings
    monkeypatch.setenv("RESEARCH_DESK_LOG_LEVEL", "DEBUG")
    assert Settings.from_env().log_level == "DEBUG"
