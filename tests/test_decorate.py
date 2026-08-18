"""Tests for decoration application, circled lists, and learnings cap."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from novaiq.decorate.decorator import apply_decorations, strip_deco_label
from novaiq.decorate.lists import circled_numbers_to_lists
from novaiq.decorate.prepare import prepare_html
from novaiq.decorate.store import Decoration
from novaiq.generate.article import SYSTEM_PROMPT
from novaiq.generate.image import LANDSCAPE_SIZE, build_eyecatch_prompt
from novaiq.models import Article, Section


def _decos() -> list[Decoration]:
    return [
        Decoration("太字", '<span class="huto">{content}</span>'),
        Decoration("黄マーカー", '<span class="ymarker">{content}</span>'),
        Decoration(
            "ポイント",
            '[st-cmemo]{content}[/st-cmemo]',
        ),
        Decoration(
            "ポイントボックス",
            '[st-mybox title="ポイント"]{content}[/st-mybox]',
        ),
        Decoration("囲み", "[st-mybox]{content}[/st-mybox]"),
        Decoration("赤マーカー", '<span class="rmarker">{content}</span>'),
    ]


class DecoratorTests(unittest.TestCase):
    def test_nested_same_name_does_not_split_shortcode(self):
        raw = (
            '<p><span data-deco="ポイントボックス">'
            '<span data-deco="ポイント">ポイント：LEDなら何でも同じではない</span>'
            "</span></p>"
        )
        out = apply_decorations(raw, enabled=True, decorations=_decos())
        self.assertNotIn("data-deco", out)
        self.assertEqual(out.count("[st-mybox"), 1)
        self.assertEqual(out.count("[/st-mybox]"), 1)
        self.assertNotIn("ポイント：", out)
        self.assertIn("LEDなら何でも同じではない", out)

    def test_lead_markers_are_applied(self):
        raw = (
            '同じ部屋でも、<span data-deco="太字">目に入る光の質</span>が違えば、'
            '<span data-deco="黄マーカー">環境側から調整すること</span>として考えられます。'
        )
        out = apply_decorations(raw, enabled=True, decorations=_decos())
        self.assertNotIn("data-deco", out)
        self.assertIn('<span class="huto">目に入る光の質</span>', out)
        self.assertIn('<span class="ymarker">環境側から調整すること</span>', out)

    def test_unclosed_marker_is_stripped(self):
        raw = '<p><span data-deco="太字">残ったタグ</p>'
        out = apply_decorations(raw, enabled=True, decorations=_decos())
        self.assertNotIn("data-deco", out)
        self.assertIn("残ったタグ", out)

    def test_marker_inside_box_stays_nested_html(self):
        raw = (
            '<span data-deco="囲み">共通するメッセージは、'
            '<span data-deco="赤マーカー">頑張りだけに任せない</span>ことです。</span>'
        )
        out = apply_decorations(raw, enabled=True, decorations=_decos())
        self.assertNotIn("data-deco", out)
        self.assertIn("[st-mybox]", out)
        self.assertIn("[/st-mybox]", out)
        self.assertIn('<span class="rmarker">頑張りだけに任せない</span>', out)

    def test_label_strip(self):
        self.assertEqual(strip_deco_label("ポイント", "ポイント：中身"), "中身")
        self.assertEqual(strip_deco_label("ポイントボックス", "ポイント：中身"), "中身")
        self.assertEqual(strip_deco_label("注意マーク", "注意：危険"), "危険")


class ListTests(unittest.TestCase):
    def test_circled_numbers_become_ol(self):
        html = (
            "<p>部屋の照明を、①直接目に入るか、②壁や天井に反射させられるか、"
            "③作業場所と休む場所で同じ光を使っていないかの3点で確認してみましょう。</p>"
        )
        out = circled_numbers_to_lists(html)
        self.assertIn("<ol>", out)
        self.assertIn("<li>直接目に入るか</li>", out)
        self.assertIn("<li>壁や天井に反射させられるか</li>", out)
        self.assertIn("<li>作業場所と休む場所で同じ光を使っていないか</li>", out)
        self.assertNotIn("①", out)

    def test_prepare_runs_lists_then_deco(self):
        html = (
            '<p><span data-deco="太字">核</span>を見る。'
            "①一つ目、②二つ目、③三つ目</p>"
        )
        out = prepare_html(html, enabled=True, decorations=_decos())
        self.assertIn('<span class="huto">核</span>', out)
        self.assertIn("<li>一つ目</li>", out)
        self.assertNotIn("data-deco", out)


class PromptAndImageTests(unittest.TestCase):
    def test_prompt_caps_learnings_and_forbids_nested_deco(self):
        self.assertIn("最大3個", SYSTEM_PROMPT)
        self.assertIn("入れ子にしない", SYSTEM_PROMPT)
        self.assertIn("装飾の名前そのもの", SYSTEM_PROMPT)
        self.assertIn("<ol>", SYSTEM_PROMPT)
        self.assertIn("光の質", SYSTEM_PROMPT)

    def test_eyecatch_prompt_is_landscape_with_blur(self):
        article = Article(
            title="テスト記事タイトル",
            slug="t",
            lead="l",
            what_you_learn=["a", "b", "c", "d"],
            reading_time_min=5,
            evidence_confidence="中",
            sections=[Section(heading="", html="<p>x</p>")],
            today_action="a",
            eyecatch_text="調子は配置から",
        )
        prompt = build_eyecatch_prompt(article, None, with_text=True)
        self.assertIn("landscape", prompt.lower())
        self.assertIn("blur", prompt.lower())
        self.assertEqual(LANDSCAPE_SIZE, "1536x1024")


if __name__ == "__main__":
    unittest.main()
