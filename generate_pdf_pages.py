#!/usr/bin/env python3
"""Generate GitHub Pages for PDF reports.

Copies PDFs from 'Research/' to 'docs/research/' and writes a Markdown
page per PDF embedding the file. The script also rebuilds docs/index.md
with links to each generated page.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "Research"
PAGES = ROOT / "docs" / "research"
INDEX = ROOT / "docs" / "index.md"


def slugify(name: str) -> str:
    """Return a filesystem-friendly slug for ``name``."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name)
    return slug.strip("-").lower()


def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    links = []
    for pdf in sorted(SRC.glob("*.pdf")):
        slug = slugify(pdf.stem)
        target = PAGES / pdf.name
        if not target.exists():
            shutil.copy2(pdf, target)
        page = PAGES / f"{slug}.md"
        page.write_text(
            f"# {pdf.stem}\n\n"
            f'<embed src="{pdf.name}" type="application/pdf" '
            f'width="100%" height="600px">\n',
            encoding="utf-8",
        )
        links.append(f"- [{pdf.stem}](research/{slug}.html)")
    INDEX.write_text(
        "# Post-Labor Economics Research\n\n" + "\n".join(links),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
