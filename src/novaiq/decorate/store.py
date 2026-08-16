"""Persistence for decorations the user enters in the admin UI.

Each decoration has a human name (e.g. "マーカー"), a code template that contains
a ``{content}`` placeholder (e.g. ``[st-marker]{content}[/st-marker]`` for
AFFINGER), an optional description, and an enabled flag. These are theme-specific
(AFFINGER) shortcodes provided by the user, so nothing is guessed here.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import List

from pathlib import Path

from ..config import DECORATIONS_PATH

DEFAULTS_PATH = Path(__file__).resolve().parent / "defaults.json"


@dataclass
class Decoration:
    name: str
    code: str  # should contain {content}
    description: str = ""
    enabled: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def _from_raw(raw) -> List[Decoration]:
    if not isinstance(raw, list):
        return []
    return [Decoration(**d) for d in raw if isinstance(d, dict) and "name" in d]


def load_default_decorations() -> List[Decoration]:
    if not DEFAULTS_PATH.exists():
        return []
    try:
        return _from_raw(json.loads(DEFAULTS_PATH.read_text(encoding="utf-8")))
    except Exception:
        return []


def load_decorations() -> List[Decoration]:
    if DECORATIONS_PATH.exists():
        try:
            items = _from_raw(json.loads(DECORATIONS_PATH.read_text(encoding="utf-8")))
            if items:
                return items
        except Exception:
            pass
    items = load_default_decorations()
    if items:
        save_decorations(items)
    return items


def save_decorations(items: List[Decoration]) -> None:
    DECORATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DECORATIONS_PATH.write_text(
        json.dumps([d.to_dict() for d in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_decoration(name: str, code: str, description: str = "") -> List[Decoration]:
    items = load_decorations()
    # Replace if the same name already exists, else append.
    items = [d for d in items if d.name != name]
    items.append(Decoration(name=name, code=code, description=description))
    save_decorations(items)
    return items


def delete_decoration(name: str) -> List[Decoration]:
    items = [d for d in load_decorations() if d.name != name]
    save_decorations(items)
    return items


def reset_to_defaults() -> List[Decoration]:
    items = load_default_decorations()
    save_decorations(items)
    return items
