"""Paper sources (OpenAlex, PubMed)."""
from __future__ import annotations

from typing import List

from ..config import Settings
from ..models import Paper
from . import openalex, pubmed


def fetch_candidates(
    settings: Settings,
    query: str,
    *,
    limit: int = 10,
    language: str = "en",
    use_pubmed: bool = True,
    min_year: int | None = None,
) -> List[Paper]:
    """Fetch candidate papers from enabled sources, sorted by citation count."""
    papers: List[Paper] = []
    try:
        papers.extend(
            openalex.search(
                settings, query, limit=limit, language=language, min_year=min_year
            )
        )
    except Exception as exc:  # keep going even if one source fails
        print(f"[sources] OpenAlex error: {exc}")

    if use_pubmed:
        try:
            papers.extend(pubmed.search(settings, query, limit=limit))
        except Exception as exc:
            print(f"[sources] PubMed error: {exc}")

    # De-duplicate by DOI (fallback: title), keep the highest citation count
    best: dict[str, Paper] = {}
    for p in papers:
        key = (p.doi or p.title).lower().strip()
        if key not in best or p.cited_by_count > best[key].cited_by_count:
            best[key] = p

    result = sorted(best.values(), key=lambda p: p.cited_by_count, reverse=True)
    return result
