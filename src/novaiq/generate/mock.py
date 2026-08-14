"""Deterministic mock article generator (no API key needed).

Used for dry-run / offline testing so the full pipeline and UI can be verified
before wiring in a real OPENAI_API_KEY.
"""
from __future__ import annotations

from ..models import Article, Paper, RelatedLink, Section
from ..templates.registry import Template


def mock_article(paper: Paper, template: Template) -> Article:
    first_author = paper.authors[0] if paper.authors else "研究チーム"
    year = paper.year or "近年"
    return Article(
        title=f"【{template.genre_label}】{paper.title[:40]} をやさしく解説",
        slug="mock-article",
        lead=(
            f"{first_author}らが{year}に発表した研究をもとに、"
            "日常で使えるポイントをやさしく整理しました。（これはモック生成のサンプル本文です）"
        ),
        what_you_learn=[
            "この研究が明らかにした中心的な発見",
            "その背景にあると考えられる仕組み",
            "今日から試せる具体的な一歩",
        ],
        reading_time_min=5,
        practice_time_min=10,
        evidence_confidence="中（査読論文だが本文はモック生成のため参考）",
        sections=[
            Section(
                heading=h,
                html=(
                    f"<p>「{h}」に関する解説がここに入ります。"
                    "実際の記事ではOpenAI APIが論文アブストラクトを基に本文を生成します。</p>"
                    "<ul><li>ポイント1</li><li>ポイント2</li></ul>"
                ),
            )
            for h in (template.outline or ["概要", "詳細", "まとめ"])
        ],
        today_action="関連する行動を1つだけ、5分でよいので今日試してみる。",
        limitations=(
            "本文はモック生成のサンプルです。研究には対象集団や条件などの限界があり、"
            "すべての人に当てはまるとは限りません。"
        ),
        related_links=[RelatedLink(label="元論文", url=paper.url or "https://openalex.org")],
        tags=[template.genre_label, "モック"],
    )
