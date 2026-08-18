"""Orchestrates: fetch paper -> generate article -> (image) -> draft / dry-run."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from .config import OUTPUT_DIR, Settings, get_settings
from .decorate import apply_decorations, load_decorations
from .generate import generate_article, generate_eyecatch, mock_article
from .models import Article, Paper
from .render import build_post_html, build_preview_page
from .sources import fetch_candidates
from .state import already_posted, mark_posted
from .templates.registry import Template, get_template

Logger = Callable[[str], None]


@dataclass
class RunResult:
    ok: bool
    dry_run: bool
    logs: List[str] = field(default_factory=list)
    paper: Optional[Paper] = None
    papers: List[Paper] = field(default_factory=list)
    article: Optional[Article] = None
    post_html: str = ""
    preview_path: Optional[Path] = None
    image_path: Optional[Path] = None
    wp_post_id: Optional[int] = None
    wp_edit_link: str = ""
    error: str = ""


def run_once(
    template_id: str,
    *,
    settings: Settings | None = None,
    language: str = "en",
    use_pubmed: bool = True,
    min_year: int | None = None,
    dry_run: bool = True,
    with_image: bool = True,
    apply_deco: bool = True,
    search_query: str | None = None,
    max_papers: int = 3,
    log: Logger | None = None,
) -> RunResult:
    settings = settings or get_settings()
    logs: List[str] = []

    def _log(msg: str) -> None:
        logs.append(msg)
        if log:
            log(msg)

    result = RunResult(ok=False, dry_run=dry_run, logs=logs)

    try:
        template: Template = get_template(template_id)
        _log(f"▶ テンプレート: {template.genre_label} / {template.name}")

        query = (search_query or template.search_query).strip()
        _log(f"🔎 論文を検索中… (query='{query}', lang={language})")
        candidates = fetch_candidates(
            settings,
            query,
            limit=20,
            language=language,
            use_pubmed=use_pubmed,
            min_year=min_year,
        )
        _log(f"   取得候補: {len(candidates)} 件")
        if not candidates:
            result.error = "論文候補が取得できませんでした。"
            _log("✖ " + result.error)
            return result

        selected: List[Paper] = []
        for cand in candidates:
            if dry_run or not already_posted(cand.source, cand.source_id, cand.doi):
                selected.append(cand)
            if len(selected) >= max(1, max_papers):
                break
        if not selected:
            selected = candidates[: max(1, max_papers)]
            _log("   （未投稿の候補が少ないため、先頭から再利用します）")

        paper = selected[0]
        result.paper = paper
        result.papers = selected
        for i, p in enumerate(selected, 1):
            _log(f"📄 採用{i}: {p.title[:70]}… (被引用 {p.cited_by_count}, {p.source})")

        # Generate article
        deco_names = [d.name for d in load_decorations() if d.enabled]
        if settings.has_openai:
            _log(f"✍  記事を生成中… (model={settings.text_model})")
            article = generate_article(
                settings,
                paper=paper,
                template=template,
                papers=selected,
                deco_names=deco_names if apply_deco else None,
            )
        else:
            _log("✍  OPENAI_API_KEY 未設定 → モック記事を生成（構造確認用）")
            article = mock_article(paper, template)
        result.article = article
        _log(f"   タイトル: {article.title}")

        if apply_deco and deco_names:
            _log(f"🎨 装飾を適用: {', '.join(deco_names[:8])}{'…' if len(deco_names) > 8 else ''}")
        if article.lead:
            article.lead = apply_decorations(article.lead, enabled=apply_deco)
        for sec in article.sections:
            sec.html = apply_decorations(sec.html, enabled=apply_deco)
        if article.closing:
            article.closing = apply_decorations(article.closing, enabled=apply_deco)

        # Image
        image_path = None
        if with_image:
            image_path = OUTPUT_DIR / "eyecatch.png"
            from .generate.image import wants_text_on_image

            kind = "文字あり" if wants_text_on_image(article) else "文字なし"
            _log(
                "🖼  アイキャッチ画像を生成中…"
                + ("" if settings.has_openai else "（プレースホルダ）")
                + f"（{kind}）"
            )
            generate_eyecatch(
                settings, article, image_path, use_api=settings.has_openai, paper=paper
            )
            result.image_path = image_path

        # Compose HTML
        post_html = build_post_html(article, paper, papers=selected)
        result.post_html = post_html

        # Always write local artifacts for inspection
        (OUTPUT_DIR / "article.json").write_text(
            article.model_dump_json(indent=2), encoding="utf-8"
        )
        preview = build_preview_page(
            article, paper, papers=selected, image_rel=image_path.name if image_path else None
        )
        preview_path = OUTPUT_DIR / "preview.html"
        preview_path.write_text(preview, encoding="utf-8")
        result.preview_path = preview_path
        _log(f"💾 生成物を出力: {OUTPUT_DIR}")

        if dry_run:
            _log("✅ dry-run 完了（WordPress へは投稿していません）")
            result.ok = True
            return result

        # Publish draft — prefer the NOVAIQ Connector (custom-header auth) when
        # configured, since it works on hosts that strip the Authorization header.
        if settings.has_connector:
            from .publish import ConnectorClient

            _log("🌐 WordPress へ接続中…(NOVAIQ Connector)")
            client = ConnectorClient(settings)
            info = client.check_connection()
            _log(f"   接続OK: {info.get('site', '?')} / admin={info.get('admin', '?')}")
            _log("📝 下書き(draft)を作成中…（画像同梱）")
            post = client.create_draft(
                title=article.title,
                content=post_html,
                category_names=[template.genre_label],
                tag_names=article.tags or None,
                image_path=image_path,
                slug=article.slug,
                status="draft",
            )
            result.wp_post_id = post.get("id")
            result.wp_edit_link = post.get("edit_link", "")
        else:
            from .publish import WordPressClient

            _log("🌐 WordPress へ接続中…(REST/Application Password)")
            client = WordPressClient(settings)
            me = client.check_connection()
            _log(f"   認証OK: {me.get('name', '?')}")

            featured = None
            if image_path and image_path.exists():
                _log("⬆  アイキャッチをアップロード中…")
                featured = client.upload_media(image_path, title=article.title)

            _log("📝 下書き(draft)を作成中…")
            post = client.create_draft(
                title=article.title,
                content=post_html,
                category_names=[template.genre_label],
                tag_names=article.tags or None,
                featured_media=featured,
                slug=article.slug,
                status="draft",
            )
            result.wp_post_id = post.get("id")
            result.wp_edit_link = (
                f"{settings.wp_url}/wp-admin/post.php?post={post.get('id')}&action=edit"
            )

        for p in selected:
            mark_posted(
                p.source, p.source_id, p.doi, article.title, result.wp_post_id, template_id
            )
        _log(f"✅ 下書き作成完了: post_id={result.wp_post_id}")
        _log(f"   編集URL: {result.wp_edit_link}")
        result.ok = True
        return result

    except Exception as exc:  # surface any failure to the UI
        result.error = f"{type(exc).__name__}: {exc}"
        _log("✖ エラー: " + result.error)
        return result
