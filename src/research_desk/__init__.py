"""Multi-agent research desk: researcher + writer + fact-checker."""
from .desk import Report, ResearchDesk
from .sources import CitationStore, MockSearch, Source, seeded_sources

__all__ = ["ResearchDesk", "Report", "MockSearch", "CitationStore",
           "Source", "seeded_sources"]
__version__ = "0.1.1"
