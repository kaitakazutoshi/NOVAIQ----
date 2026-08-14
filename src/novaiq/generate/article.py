"""Generate a structured Article from a Paper using the OpenAI API."""
from __future__ import annotations

import json

from ..config import Settings
from ..models import Article, Paper
from ..templates.registry import Template

SYSTEM_PROMPT = """あなたは自己啓発×論文を専門とする日本語のプロ編集者兼ライターです。
与えられた1本の論文情報をもとに、向上心の高い読者向けに「読みやすく・実践できる」記事を書きます。

厳守事項:
- 出力は日本語。専門用語は噛み砕く。
- 事実は与えられた論文情報の範囲で書く。存在しない数値・引用・DOIを絶対に捏造しない。
- コンディション（健康・睡眠・食事・サプリ）に触れる場合は薬機法・景表法に配慮し、効果を断定しない。
- 誇大表現を避け、限界や注意も正直に書く。
- 装飾（マーカーや囲みボックス等のショートコード）は使わない。プレーンな見出し・段落・箇条書きのみ。

必ず次のJSON形式だけを出力する（前後に説明文やコードフェンスを付けない）:
{
  "title": "魅力的で誇張しすぎない日本語タイトル",
  "slug": "short-english-slug",
  "lead": "リード文（2〜3文）",
  "what_you_learn": ["わかること1", "わかること2", "わかること3"],
  "reading_time_min": 5,
  "practice_time_min": 10,
  "evidence_confidence": "高 / 中 / 低 のいずれか＋一言理由",
  "sections": [
    {"heading": "見出し", "html": "<p>本文HTML。使ってよいタグは p, ul, ol, li, strong, em, blockquote, h3 のみ</p>"}
  ],
  "today_action": "今日すぐできる1アクション",
  "limitations": "限界・注意（研究の限界や適用範囲）",
  "related_links": [{"label": "元論文", "url": "https://..."}],
  "tags": ["タグ1", "タグ2"]
}
"""


def _build_user_prompt(paper: Paper, template: Template) -> str:
    outline = "\n".join(f"- {h}" for h in template.outline)
    return f"""# 記事テンプレート
ジャンル: {template.genre_label}
テンプレ: {template.name}
方針: {template.guidance}
見出しの骨子（参考。過不足は調整可）:
{outline}

# 元論文の情報（この範囲の事実のみ使用）
タイトル: {paper.title}
著者: {", ".join(paper.authors[:8]) if paper.authors else "不明"}
出版年: {paper.year or "不明"}
掲載: {paper.venue or "不明"}
被引用数: {paper.cited_by_count}
DOI: {paper.doi or "なし"}
URL: {paper.url or "なし"}
アブストラクト:
{paper.abstract or "（アブストラクト取得不可。タイトルと一般知識の範囲で慎重に解説する）"}

# 指示
上記テンプレに沿って、必須項目をすべて含む記事をJSONで出力してください。
related_links には少なくとも元論文へのリンク（上記URLまたはDOI）を含めること。
"""


def generate_article(settings: Settings, paper: Paper, template: Template) -> Article:
    """Call the OpenAI API and return a validated Article."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.text_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(paper, template)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    # Ensure the source paper link is always present.
    links = data.get("related_links") or []
    if paper.url and not any(paper.url in (l or {}).get("url", "") for l in links):
        links.append({"label": "元論文", "url": paper.url})
        data["related_links"] = links
    return Article.model_validate(data)
