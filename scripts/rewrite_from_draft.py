#!/usr/bin/env python3
"""Rewrite draft 424 with Terra and Sol, then post comparable WordPress drafts."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from novaiq.config import OUTPUT_DIR, get_settings
from novaiq.decorate import load_decorations, prepare_article
from novaiq.generate import comparison_banner, generate_article, generate_eyecatch, rewrite_extra, strip_for_rewrite
from novaiq.generate import image as image_mod
from novaiq.publish import ConnectorClient
from novaiq.render import build_post_html
from novaiq.sources.openalex import fetch_work
from novaiq.templates.registry import get_template

LUNA_ID = 424
PAPER_IDS = [
    "doi:10.1149/1.3568524",
    "doi:10.1136/oem.30.4.313",
    "W96857025",
]
MODELS = [
    ("gpt-5.6-terra", "GPT-5.6 Terra", "compare-terra-light-temp"),
    ("gpt-5.6-sol", "GPT-5.6 Sol", "compare-sol-light-temp"),
]


def main() -> int:
    settings = get_settings()
    client = ConnectorClient(settings)
    print("ping:", client.check_connection())

    luna = client.get_post(LUNA_ID)
    luna_title = luna.get("title") or ""
    luna_html = luna.get("raw_content") or ""
    print("luna title:", luna_title)
    print("luna html chars:", len(luna_html))

    papers = [fetch_work(settings, pid) for pid in PAPER_IDS]
    for p in papers:
        print(f"paper: {p.title[:70]}  abstract={len(p.abstract)} chars")

    template = get_template("condition_A")
    deco_names = [d.name for d in load_decorations() if d.enabled]
    extra = rewrite_extra(luna_title, strip_for_rewrite(luna_html))

    posted = []
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    orig_wants = image_mod.wants_text_on_image
    image_mod.wants_text_on_image = lambda _a: True  # type: ignore
    try:
        for model, label, slug in MODELS:
            print(f"\n=== generating with {model} ===")
            article = generate_article(
                settings,
                papers=papers,
                template=template,
                deco_names=deco_names,
                model=model,
                extra_instructions=extra,
            )
            prepare_article(article, enabled=True)
            html = comparison_banner(label) + "\n" + build_post_html(article, papers=papers)
            if "data-deco" in html:
                print("WARNING leftover data-deco")
            out_json = OUTPUT_DIR / f"article_{model.replace('.', '_')}.json"
            out_json.write_text(article.model_dump_json(indent=2), encoding="utf-8")
            image_path = OUTPUT_DIR / f"eyecatch_{model.replace('.', '_')}.png"
            print("image…")
            generate_eyecatch(settings, article, image_path, use_api=True, paper=papers[0])
            title = f"【比較 {label.split()[-1]}】{article.title}"
            post = client.create_draft(
                title=title,
                content=html,
                category_names=["コンディション"],
                tag_names=list(dict.fromkeys([*(article.tags or []), "モデル比較", label.split()[-1]])),
                image_path=image_path,
                slug=slug,
                status="draft",
            )
            print("posted:", post)
            posted.append((model, post.get("id"), title))
    finally:
        image_mod.wants_text_on_image = orig_wants

    # Label the Luna original so the three drafts sit together in the list.
    luna_banner = comparison_banner("GPT-5.6 Luna")
    if 'class="novaiq-model-compare"' not in luna_html:
        client.update_draft(
            LUNA_ID,
            title=f"【比較 Luna】{luna_title.replace('【比較 Luna】', '').strip()}",
            content=luna_banner + "\n" + luna_html,
        )
        print("labeled luna", LUNA_ID)

    print("\nDONE")
    for row in posted:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
