"""Eyecatch image generation (OpenAI) with an offline placeholder fallback."""
from __future__ import annotations

import base64
from pathlib import Path

from ..config import Settings
from ..models import Article, Paper

# ~70% of eyecatches include large Japanese text.
WITH_TEXT_RATIO = 7  # out of 10

# Landscape default. gpt-image-2 accepts 1024x1024 / 1536x1024 / 1024x1536 / auto.
LANDSCAPE_SIZE = "1536x1024"

_BG_SOLID = (
    "solid black",
    "solid black",
    "solid white",
    "solid white",
    "solid black",
    "solid white",
    "deep red",
    "vivid yellow",
)


def wants_text_on_image(article: Article) -> bool:
    """Deterministic ~70% with-text, tied to the article title."""
    n = sum(ord(c) for c in article.title) % 10
    return n < WITH_TEXT_RATIO


def text_for_image(article: Article) -> str:
    if not wants_text_on_image(article):
        return ""
    return ((article.eyecatch_text or "").strip() or article.title)


def _bg_choice(article: Article) -> str:
    """Mostly black or white; occasionally red or yellow."""
    n = sum(ord(c) for c in article.title) % 10
    if n >= 8:
        return _BG_SOLID[6 + (n - 8)]  # red or yellow
    return _BG_SOLID[n % 6]


def _placeholder_png(path: Path, title: str, line: str = "") -> Path:
    from PIL import Image, ImageDraw

    w, h = 1536, 1024
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(0, w, 2):
            t = (x / w + y / h) / 2
            r = int(10 + 60 * t)
            g = int(14 + 40 * t)
            b = int(31 + 140 * t)
            px[x, y] = (r, g, b)
            if x + 1 < w:
                px[x + 1, y] = (r, g, b)
    draw = ImageDraw.Draw(img)
    import random

    random.seed(len(title))
    for _ in range(140):
        sx, sy = random.randint(0, w - 1), random.randint(0, h - 1)
        bright = random.randint(120, 255)
        draw.ellipse([sx, sy, sx + 1, sy + 1], fill=(bright, bright, 255))
    caption = line.strip() or "NOVAIQ (placeholder)"
    draw.text((80, h // 2), caption[:40], fill=(255, 255, 255))
    img.save(path, "PNG")
    return path


def _visual_hint(article: Article, paper: Paper | None) -> str:
    """One short line that ties the image to this paper/article."""
    if paper and paper.title:
        return paper.title[:80]
    return article.title[:80]


def build_eyecatch_prompt(article: Article, paper: Paper | None, *, with_text: bool) -> str:
    """Landscape eyecatch. Background is a color field; photos must be blurred."""
    hint = _visual_hint(article, paper)
    bg = _bg_choice(article)
    photo = (
        f"Optional quiet scene related to: {hint}. "
        f"If any photograph or detailed scene is used, apply a strong blur "
        f"so overlay text stays perfectly readable. Prefer a simple {bg} field."
    )
    if with_text:
        line = (article.eyecatch_text or "").strip() or article.title
        return (
            f"Wide landscape 16:9 composition, not square. "
            f"Background: {bg} (solid or very soft gradient). {photo} "
            f"Large, extra-bold, easy-to-read Japanese text: {line}. "
            f"Centered, high contrast against the background, strong drop shadow on the letters. "
            f"No other words, no logo, no watermark."
        )
    return (
        f"Wide landscape 16:9 composition, not square. "
        f"Background: {bg} (solid or very soft gradient). {photo} "
        f"No text, no letters, no logo, no watermark."
    )


def generate_eyecatch(
    settings: Settings,
    article: Article,
    out_path: Path,
    *,
    use_api: bool,
    paper: Paper | None = None,
) -> Path:
    """Create an eyecatch image at ``out_path``. Falls back to a placeholder."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with_text = wants_text_on_image(article)
    if not (use_api and settings.has_openai):
        return _placeholder_png(out_path, article.title, text_for_image(article))

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = build_eyecatch_prompt(article, paper, with_text=with_text)
    size = settings.image_size or LANDSCAPE_SIZE
    result = client.images.generate(
        model=settings.image_model,
        prompt=prompt,
        size=size,
        quality=settings.image_quality,
        n=1,
    )
    b64 = result.data[0].b64_json
    out_path.write_bytes(base64.b64decode(b64))
    return out_path
