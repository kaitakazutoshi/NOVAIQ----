"""Prepare generated article HTML before WordPress (lists + decorations)."""
from __future__ import annotations

from typing import List

from ..models import Article
from .decorator import apply_decorations
from .lists import circled_numbers_to_lists
from .store import Decoration


def prepare_html(
    html: str,
    *,
    enabled: bool = True,
    decorations: List[Decoration] | None = None,
) -> str:
    html = circled_numbers_to_lists(html or "")
    return apply_decorations(html, enabled=enabled, decorations=decorations)


def prepare_article(
    article: Article,
    *,
    enabled: bool = True,
    decorations: List[Decoration] | None = None,
) -> Article:
    """Apply list conversion + decorations to every HTML-ish field."""
    if article.lead:
        article.lead = prepare_html(article.lead, enabled=enabled, decorations=decorations)
    for sec in article.sections:
        sec.html = prepare_html(sec.html, enabled=enabled, decorations=decorations)
    if article.closing:
        article.closing = prepare_html(
            article.closing, enabled=enabled, decorations=decorations
        )
    if len(article.what_you_learn) > 3:
        article.what_you_learn = article.what_you_learn[:3]
    return article
