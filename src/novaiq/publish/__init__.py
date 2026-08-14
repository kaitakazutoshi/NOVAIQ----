"""WordPress publishing (REST API)."""
from .wordpress import WordPressClient, WordPressError

__all__ = ["WordPressClient", "WordPressError"]
