"""OpenAlex source: multi-disciplinary, free, no API key, citation counts."""
from __future__ import annotations

from typing import List

import requests

from ..config import Settings
from ..models import Paper

API = "https://api.openalex.org/works"


def _reconstruct_abstract(inv_index: dict | None) -> str:
    """OpenAlex returns abstracts as an inverted index; rebuild plain text."""
    if not inv_index:
        return ""
    positions: list[tuple[int, str]] = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort(key=lambda x: x[0])
    return " ".join(word for _, word in positions)


def search(
    settings: Settings,
    query: str,
    *,
    limit: int = 10,
    language: str = "en",
    min_year: int | None = None,
) -> List[Paper]:
    filters = ["has_abstract:true"]
    if language and language != "any":
        filters.append(f"language:{language}")
    if min_year:
        filters.append(f"from_publication_date:{min_year}-01-01")

    params = {
        "search": query,
        "filter": ",".join(filters),
        "sort": "cited_by_count:desc",
        "per-page": min(limit, 25),
    }
    if settings.openalex_mailto:
        params["mailto"] = settings.openalex_mailto

    headers = {
        "User-Agent": f"NOVAIQ/0.1 (mailto:{settings.openalex_mailto or 'anonymous@example.com'})"
    }
    resp = requests.get(API, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    papers: List[Paper] = []
    for w in data.get("results", []):
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in w.get("authorships", [])
            if a.get("author")
        ]
        doi = (w.get("doi") or "").replace("https://doi.org/", "")
        venue = ""
        primary = w.get("primary_location") or {}
        src = primary.get("source") or {}
        if src:
            venue = src.get("display_name", "") or ""
        papers.append(
            Paper(
                source="openalex",
                source_id=w.get("id", ""),
                title=w.get("title") or w.get("display_name") or "",
                abstract=_reconstruct_abstract(w.get("abstract_inverted_index")),
                authors=[a for a in authors if a],
                year=w.get("publication_year"),
                venue=venue,
                doi=doi,
                url=w.get("doi") or w.get("id", ""),
                cited_by_count=w.get("cited_by_count", 0) or 0,
                language=w.get("language", "") or "",
            )
        )
    return papers
