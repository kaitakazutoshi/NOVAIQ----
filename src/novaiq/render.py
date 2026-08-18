"""Compose the final WordPress post HTML and a standalone preview page."""
from __future__ import annotations

import html as _html
from typing import List, Optional, Sequence
from urllib.parse import urlparse

from .models import Article, Paper


def _esc(s: str) -> str:
    return _html.escape(s, quote=True)


def source_site_name(paper: Paper) -> str:
    """Human-readable site/venue name for the discreet citation footer."""
    if paper.venue:
        return paper.venue
    url = paper.url or (f"https://doi.org/{paper.doi}" if paper.doi else "")
    if not url:
        return paper.source
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or paper.source


def source_url(paper: Paper) -> str:
    if paper.url:
        return paper.url
    if paper.doi:
        return f"https://doi.org/{paper.doi}"
    return ""


def build_post_html(
    article: Article,
    paper: Paper | None = None,
    *,
    papers: Sequence[Paper] | None = None,
    image_url: Optional[str] = None,
) -> str:
    """Build post body HTML. Citations sit last, small and unobtrusive."""
    items: List[Paper] = list(papers) if papers else ([paper] if paper else [])
    parts: list[str] = []

    learn_items = [x for x in article.what_you_learn if str(x).strip()]
    if len(learn_items) <= 1:
        learn_body = f"<p style=\"margin:0;\">{_esc(learn_items[0]) if learn_items else ''}</p>"
    else:
        learn_body = "<ul>" + "".join(f"<li>{_esc(x)}</li>" for x in learn_items) + "</ul>"
    parts.append(
        '<div class="novaiq-summary" '
        'style="border:1px solid #d0d0e0;border-radius:12px;padding:16px 20px;margin:0 0 24px;">'
        "<p style=\"margin:0 0 8px;\"><strong>この記事でわかること</strong></p>"
        f"{learn_body}"
        f"<p style=\"margin:8px 0 0;font-size:0.9em;color:#555;\">"
        f"⏱ 読了 約{article.reading_time_min}分 ／ "
        f"🔬 根拠の信頼度: {_esc(article.evidence_confidence)}</p>"
        "</div>"
    )

    if article.lead:
        parts.append(f"<p>{article.lead}</p>")

    for sec in article.sections:
        if sec.heading.strip():
            parts.append(f"<h2>{_esc(sec.heading)}</h2>")
        parts.append(sec.html)

    if article.closing:
        parts.append(f"<p>{article.closing}</p>")

    parts.append(
        '<div class="novaiq-action" '
        'style="background:#f4f1ff;border-left:4px solid #7c5cff;padding:12px 16px;margin:24px 0;">'
        f"<strong>今日の1アクション:</strong> {_esc(article.today_action)}</div>"
    )

    if article.limitations.strip():
        parts.append(
            '<p class="novaiq-note" style="font-size:0.9em;color:#666;margin:20px 0 8px;">'
            f"※ {_esc(article.limitations)}</p>"
        )

    cite_bits = []
    for p in items:
        site = source_site_name(p)
        url = source_url(p)
        bit = _esc(site)
        if url:
            bit += (
                f' · <a href="{_esc(url)}" target="_blank" rel="noopener" '
                f'style="color:#999;">{_esc(url)}</a>'
            )
        cite_bits.append(bit)
    if cite_bits:
        parts.append(
            '<p class="novaiq-cite" style="font-size:0.75em;color:#999;margin-top:32px;'
            'border-top:1px solid #eee;padding-top:12px;">'
            "出典: " + "<br>".join(cite_bits) + "</p>"
        )

    return "\n".join(parts)


def build_preview_page(
    article: Article,
    paper: Paper | None = None,
    *,
    papers: Sequence[Paper] | None = None,
    image_rel: Optional[str] = None,
) -> str:
    """Standalone dark-themed HTML page for local preview."""
    body = build_post_html(article, paper, papers=papers)
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
  .novaiq-cite {{ color:#7a82b0 !important; border-color:#2a3160 !important; }}
</style></head>
<body><div class="wrap">
{img_tag}
<h1>{_esc(article.title)}</h1>
<p>{tags}</p>
{body}
</div></body></html>"""
