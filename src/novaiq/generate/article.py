"""Generate a structured Article from papers using the OpenAI API."""
from __future__ import annotations

import json
from typing import List, Sequence

from ..config import Settings
from ..models import Article, Paper
from ..templates.registry import Template

SYSTEM_PROMPT = """あなたは自己啓発×論文を専門とする日本語のプロ編集者兼ライターです。
与えられた複数の論文を組み合わせ、厚みがあって面白い記事を書きます。
ジャンルが違っても、以下の禁止事項・骨格・装飾ルールはすべて共通です。

# 禁止事項（全ジャンル共通・絶対）
- ハッスルカルチャー禁止。「労働時間を増やす」「気合を入れて集中する」など根性論は提案しない。
- 内面操作禁止。「ポジティブに考えよう」「捉え方を変えよう」は書かない。必ず「物理的な距離をとる」「視界から消す」「環境を変える」など外的アプローチにする。
- 医療・効果の断定禁止。「これをすれば確実に治る／効果がある」は書かない（薬機法・景表法）。
- 一般論禁止。「よく寝て、バランスの良い食事を」のような誰でも言えるアドバイスは書かない。
- 政治・思想の偏りを持たない。
- 専門用語の羅列禁止。難しい言葉が出たら、直後に身近な例で一言解説する。
- 「まずは小さなことからコツコツ続けましょう」は禁止。継続できないことを読者の意志の弱さ・責任にしない。

# 骨格
- 冒頭（lead）はフックを強くする。毎回同じ型にしない。結論先出し／共感／問いかけ／読者の前提を揺さぶる、のいずれか。
- 本文は自然な文章。複数論文の知見を対話させる（補い合う・条件が違う、など）。レポートの並べ書きにしない。
- 研究デザインは必要なときだけ本文に織り込む。
- H2見出しは少なく。標準は0〜2個。短い記事はH2なしでもよい。長いときだけ3個まで。
- 末尾 closing に1〜2文。次も読みたくなる余韻。
- today_action は外的・具体的・今日できる1手。
- limitations は必須ではない。誤解や強い読みが起きそうなときだけ。不要なら空文字。
- 出典URLは本文に大きく出さない（末尾にシステムが付ける）。

# この記事でわかること（what_you_learn）
- 読者が得する中身が、一目で分かること。論文用語・専門用語を並べない。
- 箇条書きにする場合は最大3個。4つ以上は禁止。短い文章1本でもよい。
- 一般の人が読みやすい「見出し」にする。体言止めや「〜理由」「〜思考法」など、目次のように読める短文。
- 良い例（内容は記事に合わせて変える。使うのはこのうち最大3つ）:
  - LEDは「明るさ」だけでなく「光の質」で選ぶべき理由
  - 室温より重要。局所的な冷暖房の風が「体感ストレス」となる
  - 睡眠不足から心理状態まで、すべての疲労を「総ストレス量」として管理する思考法
  - 照明と室温を「配置と設定」だけで最適化
- 悪い例: 「LED照明は、明るさだけでなく光のスペクトルや色の再現性など、複数の条件で評価されること」

# 読みやすさ
- 段落を短く。1段落1メッセージ。積極的に改行する。
- ①②③と並べるときは1行に詰めない。必ず <ol><li>…</li></ol> の順序付きリストにする。導入文は別の <p> に置く。
- 伝えたい一文の前後に空段落を2つ入れる演出は使わない。

# 事実
- 出力は日本語。事実は与えられた論文情報の範囲。捏造しない。
- 複数論文があるときは、どれがどの知見か分かるように書く（著者名の連呼はしない）。

# 装飾（多めに。見て飽きない）
- ショートコード（[st-mybox] 等）は絶対に書かない。<span data-deco="名前">対象</span> だけ使う。
- data-deco は入れ子にしない。1つの要素に装飾は1つ。
- 装飾の名前そのもの（「ポイント」「注意」「囲み」など）を本文に書かない。箱の見出しはシステムが付ける。
  悪い例: <span data-deco="ポイント">ポイント：LEDなら何でも同じではない</span>
  良い例: <span data-deco="ポイント">LEDなら何でも同じではない</span>
- 太字（data-deco="太字"）は重要語・結論に多めに。黄マーカー・ポイント・注意・囲み・吹き出しも混ぜる。
- 全文マーカーは禁止。囲み/ポイント/注意は記事全体で3〜6個。
- lead にも data-deco を使ってよい（生のHTMLタグを文章として書いてはいけない）。

# アイキャッチ文言
- eyecatch_text は記事の核。文字数制限なし。読みやすいフレーズや短い文でよい。文字なしにする回だけ空文字。

必ずJSONだけを出力する:
{
  "title": "日本語タイトル",
  "slug": "short-english-slug",
  "lead": "フックの強い冒頭",
  "what_you_learn": ["見出し風の項目。箇条書きなら最大3個"],
  "reading_time_min": 6,
  "evidence_confidence": "高 または 中 または 低",
  "sections": [
    {"heading": "H2。使わない場合は空文字", "html": "<p>本文。p, ul, ol, li, strong, em, blockquote, h3 と data-deco の span のみ。①②③は ol にする</p>"}
  ],
  "closing": "締めの1〜2文",
  "today_action": "今日すぐできる外的な1アクション",
  "limitations": "注意点。不要なら空文字",
  "related_links": [{"label": "元論文", "url": "https://..."}],
  "tags": ["タグ1"],
  "eyecatch_text": "アイキャッチに載せる日本語"
}
"""


def _paper_block(papers: Sequence[Paper]) -> str:
    chunks = []
    for i, paper in enumerate(papers, 1):
        chunks.append(
            f"""## 論文{i}
タイトル: {paper.title}
著者: {", ".join(paper.authors[:8]) if paper.authors else "不明"}
出版年: {paper.year or "不明"}
掲載: {paper.venue or "不明"}
被引用数: {paper.cited_by_count}
DOI: {paper.doi or "なし"}
URL: {paper.url or "なし"}
アブストラクト:
{paper.abstract or "（アブストラクト取得不可）"}"""
        )
    return "\n\n".join(chunks)


def _build_user_prompt(
    papers: Sequence[Paper], template: Template, deco_names: list[str] | None
) -> str:
    if template.outline:
        outline = "見出しのヒント（必須ではない。0〜2個のH2で再構成してよい）:\n" + "\n".join(
            f"- {h}" for h in template.outline
        )
    else:
        outline = "H2は0〜2個。なくてもよい。"
    if deco_names:
        deco_block = f"\n# 使える装飾名\n{'、'.join(deco_names)}\n"
    else:
        deco_block = "\n# 装飾\n今回は装飾印を付けない。\n"
    n = len(papers)
    return f"""# 記事テンプレート
ジャンル: {template.genre_label}
テンプレ: {template.name}
方針: {template.guidance}
{outline}

# 使う論文（{n}本。この範囲の事実のみ。組み合わせて厚みを出す）
{_paper_block(papers)}

{deco_block}
# 指示
必須項目をJSONで出力。related_links には使った各論文のURLまたはDOIを含める。
evidence_confidence は「高」「中」「低」の1語だけ。
what_you_learn は箇条書きなら最大3個。見出しのように読める短文。
①②③は <ol><li> にする。data-deco は入れ子にしない。装飾名を本文に書かない。
eyecatch_text は記事の核（文字数制限なし）。空なら文字なし画像。
"""


def _normalize_confidence(raw: str) -> str:
    s = (raw or "中").strip()
    if s.startswith("高"):
        return "高"
    if s.startswith("低"):
        return "低"
    return "中"


def generate_article(
    settings: Settings,
    paper: Paper | None = None,
    template: Template | None = None,
    *,
    papers: Sequence[Paper] | None = None,
    deco_names: list[str] | None = None,
) -> Article:
    """Call the OpenAI API and return a validated Article."""
    from openai import OpenAI

    items: List[Paper] = list(papers) if papers else ([paper] if paper else [])
    if not items or template is None:
        raise ValueError("papers and template are required")

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=settings.text_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(items, template, deco_names)},
        ],
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    links = data.get("related_links") or []
    for p in items:
        if p.url and not any(p.url in (l or {}).get("url", "") for l in links):
            links.append({"label": p.venue or "元論文", "url": p.url})
    data["related_links"] = links
    data["closing"] = data.get("closing") or ""
    data["limitations"] = data.get("limitations") or ""
    data["eyecatch_text"] = data.get("eyecatch_text") or ""
    data["evidence_confidence"] = _normalize_confidence(str(data.get("evidence_confidence") or "中"))
    yl = data.get("what_you_learn")
    if isinstance(yl, str):
        data["what_you_learn"] = [yl]
    elif isinstance(yl, list):
        cleaned = [str(x).strip() for x in yl if str(x).strip()]
        data["what_you_learn"] = cleaned[:3] if len(cleaned) > 1 else cleaned
    data["practice_time_min"] = 0
    return Article.model_validate(data)
