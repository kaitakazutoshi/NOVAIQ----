"""Template registry.

Paid / paywall templates are deferred. For now each genre ships one free
「論文1本解説」entry. Extra formats can be appended later as short skeletons.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

GENRES: Dict[str, str] = {
    "performance": "パフォーマンス",
    "mental": "メンタル",
    "condition": "コンディション",
    "social": "社会心理",
    "habit": "ハビット",
}


@dataclass(frozen=True)
class Template:
    id: str
    genre: str
    name: str
    is_paid: bool
    search_query: str
    outline: List[str] = field(default_factory=list)
    guidance: str = ""

    @property
    def genre_label(self) -> str:
        return GENRES.get(self.genre, self.genre)


TEMPLATES: Dict[str, Template] = {}


def _register(t: Template) -> None:
    TEMPLATES[t.id] = t


# Shared prohibitions live in the system prompt (all genres).
# Outlines are hints only; the model may use 0–2 H2s.

_register(
    Template(
        id="performance_A",
        genre="performance",
        name="A：論文1本解説（無料）",
        is_paid=False,
        search_query="cognitive performance productivity focus attention learning efficiency",
        outline=["何が分かったのか", "日常への落とし込み"],
        guidance=(
            "生産性・集中・学習効率を、気合ではなく科学と環境設計で説明する。"
            "『もっと頑張る』ではなく、机の配置・通知・時間の区切りなど外的な仕組みに落とす。"
        ),
    )
)
_register(
    Template(
        id="mental_A",
        genre="mental",
        name="A：論文1本解説（無料）",
        is_paid=False,
        search_query="emotion regulation decision making stress cognitive control situation selection",
        outline=["何が分かったのか", "距離と環境でできること"],
        guidance=(
            "感情や判断の話でも、心の操作（ポジティブ思考）には落とさない。"
            "想定外でも冷静、は『場所を変える・刺激を消す・手順を外に出す』で書く。投資助言はしない。"
        ),
    )
)
_register(
    Template(
        id="condition_A",
        genre="condition",
        name="A：論文1本解説（無料）",
        is_paid=False,
        search_query="sleep circadian light meal timing environment recovery",
        outline=["何が分かったのか", "環境側で変えられること"],
        guidance=(
            "睡眠・食事・サプリ・環境。効果の断定はしない。"
            "『よく寝る・バランスの良い食事』は禁止。光、室温、食事のタイミング、部屋の配置など具体的な変数に落とす。"
        ),
    )
)
_register(
    Template(
        id="social_A",
        genre="social",
        name="A：論文1本解説（無料）",
        is_paid=False,
        search_query="social psychology bias media news judgment heuristic everyday decision",
        outline=["何が分かったのか", "身近なニュースや日常での現れ"],
        guidance=(
            "ニュースやトレンドを心理学で読む。政治的・思想的な偏りを持たない。"
            "専門用語は必ず身近な例（行列、口コミ、タイムライン）に翻訳する。時事は無料でよい。"
        ),
    )
)
_register(
    Template(
        id="habit_A",
        genre="habit",
        name="A：論文1本解説（無料）",
        is_paid=False,
        search_query="habit formation implementation intention environment design friction cue",
        outline=["続かない本当の理由", "環境側の1手"],
        guidance=(
            "習慣化・行動科学。『コツコツ意志で続ける』は禁止。"
            "続かないのは読者の弱さではなく、手がかり・摩擦・配置の問題として書く。"
        ),
    )
)


def get_template(template_id: str) -> Template:
    if template_id not in TEMPLATES:
        raise KeyError(f"Unknown template: {template_id}")
    return TEMPLATES[template_id]


def list_templates() -> List[Template]:
    return list(TEMPLATES.values())


def templates_for_genre(genre: str) -> List[Template]:
    return [t for t in TEMPLATES.values() if t.genre == genre]
