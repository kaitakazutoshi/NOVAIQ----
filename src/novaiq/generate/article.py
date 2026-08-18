"""Generate a structured Article from a Paper using the OpenAI API."""
from __future__ import annotations

import json

from ..config import Settings
from ..models import Article, Paper
from ..templates.registry import Template

SYSTEM_PROMPT = """あなたは自己啓発×論文を専門とする日本語のプロ編集者兼ライターです。
与えられた1本の論文情報をもとに、向上心の高い読者向けに「読みやすく・実践できる」記事を書きます。
ジャンルが違っても、以下の禁止事項・骨格・装飾ルールはすべて共通です。

# 禁止事項（全ジャンル共通・絶対）
- ハッスルカルチャー禁止。「労働時間を増やす」「気合を入れて集中する」など根性論は提案しない。
- 内面操作禁止。「ポジティブに考えよう」「捉え方を変えよう」は書かない。必ず「物理的な距離をとる」「視界から消す」「環境を変える」など外的アプローチにする。
- 医療・効果の断定禁止。「これをすれば確実に治る／効果がある」は書かない（薬機法・景表法）。
- 一般論禁止。「よく寝て、バランスの良い食事を」のような誰でも言えるアドバイスは書かない。
- 政治・思想の偏りを持たない。
- 専門用語の羅列禁止。必ず身近なニュースや日常の例に翻訳する。
- 「まずは小さなことからコツコツ続けましょう」は禁止。継続できないことを読者の意志の弱さ・責任にしない。

# 骨格
- 冒頭（lead）はフックを強くする。毎回同じ型にしない。結論先出し／共感／問いかけ／読者の前提を揺さぶる、のいずれか。最初の2〜3文で「続きを読みたい」と思わせる。
- 本文は自然な文章。研究デザインや参加者は、必要なときだけ本文に織り込む。毎回「方法・結果・考察」のレポート型にしない。箇条書きは本当に対比・手順のときだけ。
- H2見出しは少なく。標準は0〜2個。短い記事はH2なし（sections は heading を空文字にして html だけ）でもよい。長いときだけ3個まで。H3は使ってよいが乱用しない。
- 末尾 closing に1〜2文。今日の1アクションの予告、一言まとめ、日常への返し、次も読みたくなる余韻のいずれか。ありきたりな「参考にしてください」で終わらない。
- today_action は外的・具体的・今日できる1手（環境・配置・距離・仕組み）。気合や内面操作にしない。

# 事実
- 出力は日本語。
- 事実は与えられた論文情報の範囲。存在しない数値・引用・DOIを捏造しない。
- 限界や注意は正直に。

# 装飾（積極的に。見て飽きない）
- ショートコードそのものは書かない。装飾したい箇所だけ:
  <span data-deco="名前">対象テキスト</span>
  使える名前はユーザーメッセージの「使える装飾名」だけ。
- 積極的に使う。黄マーカー・太字・ポイント・注意・囲み・吹き出しなどを混ぜ、セクションが地の文だけにならないようにする。
- ただし全文マーカーは禁止。重要語・結論・注意・コツにピンポイント。囲み/ポイント/注意は記事全体で2〜5個。

必ず次のJSON形式だけを出力する（前後に説明文やコードフェンスを付けない）:
{
  "title": "魅力的で誇張しすぎない日本語タイトル",
  "slug": "short-english-slug",
  "lead": "フックの強い冒頭（2〜3文）",
  "what_you_learn": ["わかること1", "わかること2", "わかること3"],
  "reading_time_min": 5,
  "practice_time_min": 10,
  "evidence_confidence": "高 / 中 / 低 のいずれか＋一言理由",
  "sections": [
    {"heading": "H2。使わない場合は空文字", "html": "<p>本文。p, ul, ol, li, strong, em, blockquote, h3 と data-deco の span のみ</p>"}
  ],
  "closing": "締めの1〜2文",
  "today_action": "今日すぐできる外的な1アクション",
  "limitations": "限界・注意（研究の限界や適用範囲）",
  "related_links": [{"label": "元論文", "url": "https://..."}],
  "tags": ["タグ1", "タグ2"]
}
"""


def _build_user_prompt(paper: Paper, template: Template, deco_names: list[str] | None) -> str:
    if template.outline:
        outline = "見出しのヒント（必須ではない。0〜2個のH2で再構成してよい）:\n" + "\n".join(
            f"- {h}" for h in template.outline
        )
    else:
        outline = "H2は0〜2個。なくてもよい。"
    if deco_names:
        deco_list = "、".join(deco_names)
        deco_block = f"\n# 使える装飾名（これ以外は使わない）\n{deco_list}\n"
    else:
        deco_block = "\n# 装飾\n今回は装飾印を付けない。プレーンなHTMLのみ。\n"
    return f"""# 記事テンプレート
ジャンル: {template.genre_label}
テンプレ: {template.name}
方針: {template.guidance}
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

{deco_block}
# 指示
必須項目をすべて含む記事をJSONで出力してください。
related_links には少なくとも元論文へのリンク（上記URLまたはDOI）を含めること。
"""


def generate_article(
    settings: Settings,
    paper: Paper,
    template: Template,
    *,
    deco_names: list[str] | None = None,
) -> Article:
    """Call the OpenAI API and return a validated Article."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.text_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(paper, template, deco_names)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    links = data.get("related_links") or []
    if paper.url and not any(paper.url in (l or {}).get("url", "") for l in links):
        links.append({"label": "元論文", "url": paper.url})
        data["related_links"] = links
    if not data.get("closing"):
        data["closing"] = ""
    return Article.model_validate(data)
