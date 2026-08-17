"""Eyecatch image generation (OpenAI) with an offline placeholder fallback."""
from __future__ import annotations

import base64
import math
from pathlib import Path

from ..config import Settings
from ..models import Article


def _placeholder_png(path: Path, title: str) -> Path:
    """Generate a space-themed gradient placeholder (no API needed)."""
    from PIL import Image, ImageDraw

    w, h = 1200, 630
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
    # A few "stars"
    import random

    random.seed(len(title))
    for _ in range(140):
        sx, sy = random.randint(0, w - 1), random.randint(0, h - 1)
        bright = random.randint(120, 255)
        draw.ellipse([sx, sy, sx + 1, sy + 1], fill=(bright, bright, 255))
    draw.text((60, h - 70), "NOVAIQ (placeholder eyecatch)", fill=(200, 205, 255))
    img.save(path, "PNG")
    return path


def generate_eyecatch(
    settings: Settings, article: Article, out_path: Path, *, use_api: bool
) -> Path:
    """Create an eyecatch image at ``out_path``. Falls back to a placeholder."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not (use_api and settings.has_openai):
        return _placeholder_png(out_path, article.title)

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = (
        "A modern, clean, futuristic hero illustration for a self-improvement science "
        f"article titled '{article.title}'. Abstract, elegant, cosmic/space vibe, "
        "deep indigo and violet palette, subtle glow, no text, no words."
    )
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
