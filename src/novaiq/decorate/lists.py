"""Turn circled-number sequences (①②③) into real ordered lists."""
from __future__ import annotations

import re

_CIRCLE_SPLIT = re.compile(r"[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]")
_P_RE = re.compile(r"<p>(.*?)</p>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")
_TRAILING_COUNT = re.compile(r"(の[0-9０-９一二三四五六七八九十]+点.*)$")


def _plain(html: str) -> str:
    return _TAG_RE.sub("", html)


def circled_numbers_to_lists(html: str) -> str:
    """Replace ①…②…③… inside ``<p>`` blocks with ``<ol><li>``.

    Prefix HTML is preserved (so decorations in the same paragraph survive).
    """
    if not html or "①" not in html:
        return html

    def repl(m: re.Match) -> str:
        inner = m.group(1)
        if "①" not in inner or "②" not in inner:
            return m.group(0)
        parts = _CIRCLE_SPLIT.split(inner)
        if len(parts) < 3:
            return m.group(0)
        prefix_html = parts[0].rstrip()
        items: list[str] = []
        for chunk in parts[1:]:
            item = chunk.strip().strip("、,， ").rstrip("。")
            if _plain(item).strip():
                items.append(item)
        if len(items) < 2:
            return m.group(0)
        last_plain = _plain(items[-1]).strip()
        suffix_html = ""
        tm = _TRAILING_COUNT.search(last_plain)
        if tm:
            suffix_plain = tm.group(1)
            items[-1] = items[-1].replace(suffix_plain, "").rstrip("、。 ")
            suffix_html = suffix_plain
            items = [x for x in items if _plain(x).strip()]
            if len(items) < 2:
                return m.group(0)
        ol = "<ol>" + "".join(f"<li>{item}</li>" for item in items) + "</ol>"
        bits: list[str] = []
        if _plain(prefix_html).strip():
            bits.append(f"<p>{prefix_html}</p>")
        bits.append(ol)
        if suffix_html:
            bits.append(f"<p>{suffix_html}</p>")
        return "".join(bits)

    return _P_RE.sub(repl, html)
