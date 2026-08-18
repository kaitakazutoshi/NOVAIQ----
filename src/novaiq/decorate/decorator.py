"""Apply user-defined decorations to article HTML.

Convention: the article generator wraps phrases in
``<span data-deco="名前">...</span>`` (or ``div``). When decoration is enabled,
each marker is replaced by the matching decoration's ``code`` template with
``{content}`` substituted. Unknown/disabled names become plain content.

Markers are resolved innermost-first, and matching close tags are found by
counting nested ``span``/``div`` depth. A naive non-greedy regex would close on
the first ``</span>`` (including an inner marker or ``<span class="huto">``),
which split AFFINGER shortcodes in half and leaked raw ``data-deco`` tags.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .store import Decoration, load_decorations

_OPEN_RE = re.compile(
    r'<(span|div)\s+data-deco="(?P<name>[^"]+)"\s*>',
    re.IGNORECASE,
)

_LEFTOVER_DECO_RE = re.compile(
    r"</?(?:span|div)\s+[^>]*data-deco=(?:\"[^\"]*\"|'[^']*')[^>]*>",
    re.IGNORECASE,
)

# If the model writes the decoration name as a visible label ("ポイント：").
_BOXISH = (
    "ポイント",
    "ポイントボックス",
    "注意",
    "注意マーク",
    "メモ",
    "はてな",
    "はてなボックス",
    "囲み",
    "吹き出し",
    "会話",
    "チェック",
)


def _label_candidates(name: str) -> list[str]:
    names = [name]
    for suffix in ("ボックス", "マーク"):
        if name.endswith(suffix):
            names.append(name[: -len(suffix)])
    seen: list[str] = []
    for n in names:
        n = n.strip()
        if n and n not in seen:
            seen.append(n)
    seen.sort(key=len, reverse=True)
    return seen


def strip_deco_label(name: str, content: str) -> str:
    """Drop a leading 'ポイント：' / '注意：' the model copied from the deco name."""
    text = content.lstrip()
    for label in _label_candidates(name):
        for sep in ("：", ":", "。", " "):
            prefix = label + sep
            if text.startswith(prefix):
                return text[len(prefix) :].lstrip()
        if text == label:
            return ""
    return content


def strip_leftover_deco_tags(html: str) -> str:
    """Remove any leftover data-deco tags the matcher could not pair."""
    return _LEFTOVER_DECO_RE.sub("", html or "")


def _close_tag_at(html: str, tag: str, from_idx: int) -> Optional[re.Match]:
    """Find the ``</tag>`` that matches an opener ending at ``from_idx``, by depth."""
    depth = 1
    i = from_idx
    open_re = re.compile(rf"<{re.escape(tag)}\b[^>]*>", re.IGNORECASE)
    close_re = re.compile(rf"</{re.escape(tag)}\s*>", re.IGNORECASE)
    while i < len(html):
        m_open = open_re.search(html, i)
        m_close = close_re.search(html, i)
        if not m_close:
            return None
        if m_open and m_open.start() < m_close.start():
            depth += 1
            i = m_open.end()
            continue
        depth -= 1
        if depth == 0:
            return m_close
        i = m_close.end()
    return None


def _innermost_marker(html: str) -> Optional[Tuple[int, int, str, str]]:
    """Return (start, end, name, content) for the leftmost innermost data-deco."""
    for m in _OPEN_RE.finditer(html):
        tag = m.group(1)
        name = m.group("name")
        closer = _close_tag_at(html, tag, m.end())
        if closer is None:
            continue
        content = html[m.end() : closer.start()]
        if _OPEN_RE.search(content):
            continue
        return m.start(), closer.end(), name, content
    return None


def apply_decorations(
    html: str, *, enabled: bool, decorations: List[Decoration] | None = None
) -> str:
    """Return html with decoration markers resolved (or stripped if disabled)."""
    if not html:
        return html or ""
    decos = {d.name: d for d in (decorations if decorations is not None else load_decorations())}

    def replace_one(name: str, content: str) -> str:
        if name in _BOXISH or any(name.startswith(b) for b in _BOXISH):
            content = strip_deco_label(name, content)
        deco = decos.get(name)
        already_shortcode = bool(
            re.search(r"\[st-(?:mybox|cmemo|minihukidashi|kaiwa)", content)
        )
        if already_shortcode:
            inner_text = re.sub(r"\[/?st-[^\]]*\]", "", content).strip()
            if (
                enabled
                and deco
                and deco.enabled
                and "{content}" in deco.code
                and "[st-" in deco.code
            ):
                return deco.code.replace("{content}", inner_text)
            return content
        if enabled and deco and deco.enabled and "{content}" in deco.code:
            return deco.code.replace("{content}", content)
        return content

    out = html
    for _ in range(64):
        found = _innermost_marker(out)
        if not found:
            break
        start, end, name, content = found
        out = out[:start] + replace_one(name, content) + out[end:]
    return strip_leftover_deco_tags(out)
