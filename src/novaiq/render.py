"""Compose the final WordPress post HTML and a standalone preview page."""
from __future__ import annotations

import html as _html
from typing import Optional

from .models import Article, Paper


def _esc(s: str) -> str:
    return _html.escape(s, quote=True)


def build_post_html(article: Article, paper: Paper, *, image_url: Optional[str] = None) -> str:
    """Build clean, theme-independent post body HTML (no decoration in Phase 1)."""
    parts: list[str] = []

    # Summary / info box (required fields at a glance)
    learn = "".join(f"<li>{_esc(x)}</li>" for x in article.what_you_learn)
    parts.append(
        '<div class="novaiq-summary" '
        'style="border:1px solid #d0d0e0;border-radius:12px;padding:16px 20px;margin:0 0 24px;">'
        "<p style=\"margin:0 0 8px;\"><strong>この記事でわかること</strong></p>"
        f"<ul>{learn}</ul>"
        f"<p style=\"margin:8px 0 0;font-size:0.9em;color:#555;\">"
        f"⏱ 読了 約{article.reading_time_min}分 ／ 🛠 実践 約{article.practice_time_min}分 ／ "
        f"🔬 根拠の信頼度: {_esc(article.evidence_confidence)}</p>"
        "</div>"
    )

    if article.lead:
        parts.append(f"<p>{_esc(article.lead)}</p>")

    # Body sections (html is model-produced; kept as-is)
    for sec in article.sections:
        parts.append(f"<h2>{_esc(sec.heading)}</h2>")
        parts.append(sec.html)

    # Today's action
    parts.append(
        '<div class="novaiq-action" '
        'style="background:#f4f1ff;border-left:4px solid #7c5cff;padding:12px 16px;margin:24px 0;">'
        f"<strong>今日の1アクション:</strong> {_esc(article.today_action)}</div>"
    )

    # Limitations
    parts.append("<h2>限界・注意</h2>")
    parts.append(f"<p>{_esc(article.limitations)}</p>")

    # Related links
    if article.related_links:
        links = "".join(
            f'<li><a href="{_esc(l.url)}" target="_blank" rel="noopener">{_esc(l.label)}</a></li>'
            for l in article.related_links
        )
        parts.append("<h2>関連リンク</h2>")
        parts.append(f"<ul>{links}</ul>")

    # Source citation
    parts.append(
        '<p style="font-size:0.85em;color:#666;margin-top:24px;">'
        f"出典: {_esc(paper.short_citation())}"
        + (f' DOI: <a href="https://doi.org/{_esc(paper.doi)}">{_esc(paper.doi)}</a>' if paper.doi else "")
        + f"（被引用数 {paper.cited_by_count}）</p>"
    )

    return "\n".join(parts)


def build_preview_page(article: Article, paper: Paper, *, image_rel: Optional[str] = None) -> str:
    """Standalone dark-themed HTML page for local preview."""
    body = build_post_html(article, paper)
    img_tag = (
        f'<img src="{_esc(image_rel)}" alt="eyecatch" '
        'style="width:100%;border-radius:16px;margin:0 0 24px;">'
        if image_rel
        else ""
    )
    tags = " ".join(f'<span class="tag">#{_esc(t)}</span>' for t in article.tags)
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(article.title)} — NOVAIQ preview</title>
<style>
  body {{ background:#0a0e1f; color:#e6e9ff; font-family:-apple-system,'Segoe UI',sans-serif;
         line-height:1.85; margin:0; padding:40px 16px; }}
  .wrap {{ max-width:760px; margin:0 auto; background:#121734; padding:32px 40px;
          border-radius:20px; box-shadow:0 0 60px rgba(124,92,255,.25); }}
  h1 {{ font-size:1.9em; line-height:1.3; }}
  h2 {{ color:#b3a4ff; border-bottom:1px solid #2a3160; padding-bottom:6px; margin-top:32px; }}
  a {{ color:#8fb4ff; }}
  .tag {{ color:#9a8cff; font-size:.85em; margin-right:6px; }}
  .novaiq-summary {{ background:#0e1330; border-color:#2a3160 !important; }}
  .novaiq-action {{ background:#1a1640 !important; }}
</style></head>
<body><div class="wrap">
{img_tag}
<h1>{_esc(article.title)}</h1>
<p>{tags}</p>
{body}
</div></body></html>"""
