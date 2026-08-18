"""Rewrite an existing article with a different text model (comparison experiments)."""
from __future__ import annotations

import re

REWRITE_INSTRUCTIONS = """
# リライト実験（人間の編集者に近づける）
下のLuna稿は事実関係は使ってよいが、文章の型をコピーしない。
いまの稿は説明が整いすぎて、AIが書いた説明文に見えやすい。同じ3本の論文の範囲だけで、人間のウェブ編集者が書いたように書き直す。

- 文の長さをばらす。同じ構文（「〜ということです」「〜として考えられます」）を続けない
- 「つまり」「一方」「たとえば」の機械的な接続を減らす
- 論文の要約を並べるのではなく、読者の部屋・身体の話を先に置き、論文は後から支える
- タイトル・リード・今日の1アクションも、意味は保ちつつ言い回しを変える
- 新しい効果や医療的な断定は足さない。論文にない事実は書かない
- ショートコードは書かない。data-deco の span のみ
"""


def strip_for_rewrite(html: str) -> str:
    """Turn decorated HTML into readable source text for a rewrite prompt."""
    text = html or ""
    text = re.sub(r"\[/?st-[^\]]*\]", "", text)
    text = re.sub(r"<h2[^>]*>", "\n## ", text)
    text = re.sub(r"<h3[^>]*>", "\n### ", text)
    text = re.sub(r"</h[23]>", "\n", text)
    text = re.sub(r"<li[^>]*>", "\n- ", text)
    text = re.sub(r"</li>", "", text)
    text = re.sub(r"</?ol[^>]*>", "\n", text)
    text = re.sub(r"</?ul[^>]*>", "\n", text)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def rewrite_extra(luna_title: str, luna_body: str) -> str:
    return (
        REWRITE_INSTRUCTIONS
        + "\n# Luna稿（下書き424。型をコピーせず、事実だけ借りる）\n"
        + f"タイトル: {luna_title}\n\n"
        + luna_body
        + "\n"
    )


def comparison_banner(model_label: str) -> str:
    return (
        '<p class="novaiq-model-compare" '
        'style="font-size:0.9em;color:#444;background:#f7f7fb;border:1px dashed #c5c5d6;'
        'padding:10px 14px;border-radius:10px;margin:0 0 22px;">'
        f"<strong>モデル比較実験</strong>　この下書きは "
        f"<strong>{model_label}</strong> で書いています。"
        "公開用ではなく、文章の違いを見るための下書きです。</p>"
    )
