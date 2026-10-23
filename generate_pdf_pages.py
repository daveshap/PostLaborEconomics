#!/usr/bin/env python3
"""Generate GitHub Pages for PDF reports.

For each PDF in 'Research/' that is not on the website yet, copies it to 'docs/research/', writes its page
(front matter only; the site's "report" layout draws the page), and adds it under "Recently added" at the
end of the research library (docs/_includes/pages/research.html), from where it can be moved into the right
theme by hand.

Pages and files that already exist are left alone, a PDF already published under another name is skipped,
and nothing is ever deleted.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
from urllib.parse import quote
import hashlib
import shutil
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "Research"
PAGES = ROOT / "docs" / "research"
LIBRARY = ROOT / "docs" / "_includes" / "pages" / "research.html"
MARKER = "<!-- end of library -->"
RECENT_START = '<section class="recently-added" id="recently-added" aria-labelledby="recently-added-title">'


def slugify(name: str) -> str:
    """Return a filesystem-friendly slug for ``name``."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", name)
    return slug.strip("-").lower()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def yaml_str(value: str) -> str:
    return '"' + value.replace("\\", "").replace('"', '\\"') + '"'


def page_text(title: str, pdf: Path) -> str:
    """The page for one report: front matter only."""
    size = pdf.stat().st_size
    size_text = f"PDF, {size / 1048576:.1f} MB" if size >= 1048576 else f"PDF, {max(1, round(size / 1024))} KB"
    fields = {
        "layout": "report", "title": title, "subtitle": "", "description": f"{title}: a Post-Labor Economics research report (PDF).",
        "nav": "research", "theme": "Recently added", "theme_id": "recently-added",
        "pdf": pdf.name, "pdf_url": quote(pdf.name), "pdf_size": size_text,
        "prev_url": "", "prev_title": "", "next_url": "", "next_title": "",
    }
    return "---\n" + "".join(f"{k}: {yaml_str(v)}\n" for k, v in fields.items() if v) + "---\n"


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
        page.write_text(page_text(pdf.stem, target), encoding="utf-8")
        added.append(f'<li><a href="{slug}.html">{escape(pdf.stem)}</a></li>')
    if added and LIBRARY.exists():
        library = LIBRARY.read_text(encoding="utf-8")
        if RECENT_START not in library:
            section = (f'{RECENT_START}\n<h2 id="recently-added-title">Recently added</h2>\n'
                       '<ul class="recent-list">\n</ul>\n</section>\n')
            library = library.replace(MARKER, section + MARKER)
        head, tail = library.split('<ul class="recent-list">\n', 1)
        library = head + '<ul class="recent-list">\n' + "".join(a + "\n" for a in added) + tail
        LIBRARY.write_text(library, encoding="utf-8")
    print(f"{len(added)} new report page(s)")
    for line in added:
        print("  " + line)


if __name__ == "__main__":
    main()
