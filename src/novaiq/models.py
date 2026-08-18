"""Shared data models for papers and generated articles."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Paper(BaseModel):
    """A scientific paper fetched from a source (OpenAlex, PubMed, ...)."""

    source: str
    source_id: str
    title: str
    abstract: str = ""
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: str = ""
    doi: str = ""
    url: str = ""
    cited_by_count: int = 0
    language: str = ""

    def short_citation(self) -> str:
        author = self.authors[0] if self.authors else "Unknown"
        if len(self.authors) > 1:
            author += " et al."
        year = f" ({self.year})" if self.year else ""
        return f"{author}{year}. {self.title}."


class RelatedLink(BaseModel):
    label: str
    url: str


class Section(BaseModel):
    heading: str
    html: str


class Article(BaseModel):
    """Structured article output. Renders to clean HTML (theme-independent)."""

    title: str
    slug: str = ""
    lead: str = ""
    # Required editorial fields (enforced for every article)
    what_you_learn: List[str] = Field(..., min_length=3, max_length=3)
    reading_time_min: int = Field(..., ge=1)
    practice_time_min: int = Field(..., ge=0)
    evidence_confidence: str
    sections: List[Section] = Field(..., min_length=1)
    closing: str = ""
    today_action: str
    limitations: str
    related_links: List[RelatedLink] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
