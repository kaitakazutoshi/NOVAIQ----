"""Eyecatch image generation (OpenAI) with an offline placeholder fallback."""
from __future__ import annotations

import base64
from pathlib import Path

from ..config import Settings
from ..models import Article, Paper

# ~70% of eyecatches include large Japanese text.
WITH_TEXT_RATIO = 7  # out of 10


def wants_text_on_image(article: Article) -> bool:
    """Deterministic ~70% with-text, tied to the article title."""
    n = sum(ord(c) for c in article.title) % 10
    return n < WITH_TEXT_RATIO


def text_for_image(article: Article) -> str:
    if not wants_text_on_image(article):
        return ""
    return ((article.eyecatch_text or "").strip() or article.title)


def _placeholder_png(path: Path, title: str, line: str = "") -> Path:
    from PIL import Image, ImageDraw

    w, h = 1024, 1024
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
    draw.text((60, h // 2), caption[:24], fill=(255, 255, 255))
    img.save(path, "PNG")
    return path


def _visual_hint(article: Article, paper: Paper | None) -> str:
    """One short line that ties the image to this paper/article."""
    if paper and paper.title:
        return paper.title[:80]
    return article.title[:80]


def build_eyecatch_prompt(article: Article, paper: Paper | None, *, with_text: bool) -> str:
    """Keep prompts short. Visual must match the paper; text style is a fixed template."""
    hint = _visual_hint(article, paper)
    if with_text:
        line = (article.eyecatch_text or "").strip() or article.title
        return (
            f"Simple uncluttered background, one color or soft gradient. "
            f"Quiet scene related to: {hint}. "
            f"Large, extra-bold, easy-to-read Japanese text: {line}. "
            f"Centered, high contrast, strong drop shadow on the letters. "
            f"No other words, no logo, no watermark."
        )
    return (
        f"Simple uncluttered background. "
        f"Quiet scene related to: {hint}. "
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
    result = client.images.generate(
        model=settings.image_model,
        prompt=prompt,
        size=settings.image_size,
        quality=settings.image_quality,
        n=1,
    )
    b64 = result.data[0].b64_json
    out_path.write_bytes(base64.b64decode(b64))
    return out_path
