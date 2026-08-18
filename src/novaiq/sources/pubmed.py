"""PubMed source via NCBI E-utilities (biomedical / life sciences)."""
from __future__ import annotations

from typing import List

import requests

from ..config import Settings
from ..models import Paper

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def search(settings: Settings, query: str, *, limit: int = 10) -> List[Paper]:
    common = {"db": "pubmed", "retmode": "json"}
    if settings.ncbi_api_key:
        common["api_key"] = settings.ncbi_api_key

    r = requests.get(
        ESEARCH,
        params={**common, "term": query, "retmax": min(limit, 20), "sort": "relevance"},
        timeout=30,
    )
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []

    r2 = requests.get(ESUMMARY, params={**common, "id": ",".join(ids)}, timeout=30)
    r2.raise_for_status()
    result = r2.json().get("result", {})

    papers: List[Paper] = []
    for uid in result.get("uids", []):
        item = result.get(uid, {})
        authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
        doi = ""
        for aid in item.get("articleids", []):
            if aid.get("idtype") == "doi":
                doi = aid.get("value", "")
        year = None
        pubdate = item.get("pubdate", "")
        if pubdate[:4].isdigit():
            year = int(pubdate[:4])
        papers.append(
            Paper(
                source="pubmed",
                source_id=uid,
                title=item.get("title", ""),
                abstract="",  # esummary omits abstracts; fetched separately if needed
                authors=authors,
                year=year,
                venue=item.get("fulljournalname", "") or item.get("source", ""),
                doi=doi,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                cited_by_count=0,  # PubMed does not expose citation counts
                language="",
            )
        )
    return papers
