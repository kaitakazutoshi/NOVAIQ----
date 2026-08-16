"""Command-line runner for the NOVAIQ pipeline (useful for headless testing).

Examples:
    python cli.py --template performance_A --dry-run
    python cli.py --template performance_A --no-dry-run   # posts a draft
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from novaiq.pipeline import run_once  # noqa: E402
from novaiq.templates.registry import list_templates  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVAIQ auto-poster")
    ap.add_argument("--template", default="performance_A")
    ap.add_argument("--language", default="en", choices=["en", "ja", "any"])
    ap.add_argument("--no-pubmed", action="store_true")
    ap.add_argument("--min-year", type=int, default=None)
    ap.add_argument("--no-image", action="store_true")
    ap.add_argument("--no-deco", action="store_true", help="skip AFFINGER decorations")
    ap.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    ap.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    ap.add_argument("--list", action="store_true", help="list templates and exit")
    args = ap.parse_args()

    if args.list:
        for t in list_templates():
            print(f"{t.id:20} {t.genre_label:8} {t.name}")
        return 0

    res = run_once(
        args.template,
        language=args.language,
        use_pubmed=not args.no_pubmed,
        min_year=args.min_year,
        dry_run=args.dry_run,
        with_image=not args.no_image,
        apply_deco=not args.no_deco,
        log=print,
    )
    print("\n--- RESULT ---")
    print("ok:", res.ok, "| dry_run:", res.dry_run)
    if res.error:
        print("error:", res.error)
        return 1
    if res.preview_path:
        print("preview:", res.preview_path)
    if res.wp_post_id:
        print("wp_post_id:", res.wp_post_id)
    return 0 if res.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
