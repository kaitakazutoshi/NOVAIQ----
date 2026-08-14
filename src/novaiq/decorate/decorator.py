"""Apply user-defined decorations to article HTML.

Phase 1 intentionally keeps decoration OFF: articles are generated as clean,
theme-independent HTML. This module provides the hook so that, once the user has
entered their real AFFINGER shortcodes in the admin UI, decoration can be turned
on centrally without touching generation logic.

Convention: the article generator may wrap content in
``<span data-deco="マーカー">...</span>`` markers. When decoration is enabled,
each such span is replaced by the matching decoration's ``code`` template with
``{content}`` substituted. Unknown/disabled names are left as plain content.
"""
from __future__ import annotations

import re
from typing import List

from .store import Decoration, load_decorations

_DECO_RE = re.compile(
    r'<span\s+data-deco="(?P<name>[^"]+)"\s*>(?P<content>.*?)</span>',
    re.DOTALL,
)


def apply_decorations(html: str, *, enabled: bool, decorations: List[Decoration] | None = None) -> str:
    """Return html with decoration markers resolved (or stripped if disabled)."""
    decos = {d.name: d for d in (decorations if decorations is not None else load_decorations())}

    def repl(m: re.Match) -> str:
        name = m.group("name")
        content = m.group("content")
        deco = decos.get(name)
        if enabled and deco and deco.enabled and "{content}" in deco.code:
            return deco.code.replace("{content}", content)
        return content  # decoration off or undefined -> keep plain content

    return _DECO_RE.sub(repl, html)
