#!/usr/bin/env python3
"""Generate GitHub Pages for PDF reports.

For each PDF in 'Research/' that is not on the website yet, copies it to 'docs/research/', writes a page that
shows it, and lists the page under "Recently added" at the end of the research library
(docs/research/index.md), from where it can be moved into the right theme by hand.

Pages and files that already exist are left alone, a PDF already published under another name is skipped,
and nothing is ever deleted.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote
import hashlib
import shutil
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "Research"
PAGES = ROOT / "docs" / "research"
LIBRARY = PAGES / "index.md"
RECENT = "## Recently added"


def slugify(name: str) -> str:
    """Return a filesystem-friendly slug for ``name``."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name)
    return slug.strip("-").lower()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_text(title: str, pdf_name: str) -> str:
    """The page for one report: its title, a download link, and the PDF shown inline."""
    return (
        f"# {title}\n\n"
        f"[← Research library](./) · [Download the PDF]({quote(pdf_name)})\n\n"
        f'<embed src="{pdf_name}" type="application/pdf" width="100%" height="800px">\n'
    )


def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    published = {digest(p) for p in PAGES.glob("*.pdf")}
    added = []
    for pdf in sorted(SRC.glob("*.pdf")):
        slug = slugify(pdf.stem)
        page = PAGES / f"{slug}.md"
        target = PAGES / pdf.name
        if page.exists() or (not target.exists() and digest(pdf) in published):
            continue
        if not target.exists():
            shutil.copy2(pdf, target)
        page.write_text(page_text(pdf.stem, pdf.name), encoding="utf-8")
        added.append(f"- [{pdf.stem}]({slug}.html)")
    if added:
        library = LIBRARY.read_text(encoding="utf-8") if LIBRARY.exists() else "# Research library\n"
        if RECENT not in library:
            library = library.rstrip("\n") + f"\n\n{RECENT}\n"
        LIBRARY.write_text(library.rstrip("\n") + "\n" + "\n".join(added) + "\n", encoding="utf-8")
    print(f"{len(added)} new report page(s)")
    for line in added:
        print("  " + line)


if __name__ == "__main__":
    main()
