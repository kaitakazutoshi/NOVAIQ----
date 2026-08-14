"""Article templates (genre x template)."""
from .registry import (
    GENRES,
    TEMPLATES,
    Template,
    get_template,
    list_templates,
    templates_for_genre,
)

__all__ = [
    "GENRES",
    "TEMPLATES",
    "Template",
    "get_template",
    "list_templates",
    "templates_for_genre",
]
