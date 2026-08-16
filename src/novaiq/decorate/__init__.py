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
from .decorator import apply_decorations

__all__ = [
    "Decoration",
    "add_decoration",
    "delete_decoration",
    "load_decorations",
    "save_decorations",
    "load_default_decorations",
    "reset_to_defaults",
    "apply_decorations",
]
