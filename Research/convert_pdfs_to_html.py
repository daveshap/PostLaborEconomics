"""Batch convert PDFs in this directory to HTML files for GitHub Pages.

This script uses pdfminer.six to preserve layout when converting PDFs to HTML.
The generated files are placed in ``../docs/research`` with the same base name
as the source PDF.

Example usage::

    python convert_pdfs_to_html.py

You must install ``pdfminer.six`` first::

    pip install pdfminer.six
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from pdfminer.high_level import extract_text
except ImportError as exc:  # pragma: no cover - library may not be installed during testing
    raise SystemExit(
        "pdfminer.six is required. Install it with `pip install pdfminer.six`"
    ) from exc


OUTPUT_DIR = Path("..") / "docs" / "research"


def convert_pdf_to_html(pdf_path: Path) -> None:
    """Convert ``pdf_path`` to an HTML file in :data:`OUTPUT_DIR`."""
    html = extract_text(str(pdf_path), output_type="html")
    title = pdf_path.stem
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"{title}.html"
    with out_file.open("w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    for entry in os.listdir('.'):
        if entry.lower().endswith('.pdf') and os.path.isfile(entry):
            pdf_path = Path(entry)
            print(f"Converting {pdf_path}")
            try:
                convert_pdf_to_html(pdf_path)
            except Exception as e:  # pragma: no cover - runtime feedback
                print(f"Failed to convert {pdf_path}: {e}")


if __name__ == "__main__":
    main()
