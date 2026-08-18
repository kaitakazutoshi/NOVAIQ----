"""User-managed decoration mapping (name -> shortcode/HTML template)."""
from .store import (
    Decoration,
    add_decoration,
    delete_decoration,
    load_decorations,
    save_decorations,
    load_default_decorations,
    reset_to_defaults,
)
from .decorator import apply_decorations, strip_leftover_deco_tags
from .prepare import prepare_article, prepare_html

__all__ = [
    "Decoration",
    "add_decoration",
    "delete_decoration",
    "load_decorations",
    "save_decorations",
    "load_default_decorations",
    "reset_to_defaults",
    "apply_decorations",
    "strip_leftover_deco_tags",
    "prepare_article",
    "prepare_html",
]
