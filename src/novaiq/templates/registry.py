"""Template registry.

Templates are pure data: adding the remaining 2 templates per genre (to reach
3 per genre / 15 total) is just appending ``Template(...)`` entries here — no
code changes elsewhere are required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# Genre keys are stable ids; labels are Japanese display names.
GENRES: Dict[str, str] = {
    "performance": "パフォーマンス",
    "mental": "メンタル",
    "condition": "コンディション",
    "social": "社会心理",
    "habit": "ハビット",
}


@dataclass(frozen=True)
class Template:
    id: str  # e.g. "performance_A"
    genre: str  # key in GENRES
    name: str  # display name
    is_paid: bool  # free vs paid tier
    search_query: str  # query sent to paper sources
    outline: List[str] = field(default_factory=list)  # heading skeleton
    guidance: str = ""  # extra instruction fragment for the LLM

    @property
    def genre_label(self) -> str:
        return GENRES.get(self.genre, self.genre)


# Phase 1 ships performance_A. The rest are stubs to be filled in later.
TEMPLATES: Dict[str, Template] = {}


def _register(t: Template) -> None:
    TEMPLATES[t.id] = t


_register(
    Template(
        id="performance_A",
        genre="performance",
        name="A：論文1本解説（無料）",
        is_paid=False,
        search_query="cognitive performance productivity focus learning efficiency",
        outline=[
            "この研究が扱った問題",
            "研究デザインと参加者",
            "わかったこと（主要な結果）",
            "なぜそうなるのか（メカニズム）",
            "日常への落とし込み",
        ],
        guidance=(
            "1本の論文をわかりやすく解説する。専門用語は噛み砕き、"
            "生産性・集中・学習効率の観点から、気合ではなく科学として説明する。"
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
