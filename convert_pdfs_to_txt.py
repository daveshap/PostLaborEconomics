#!/usr/bin/env python3
"""
Batch convert the PDFs in ./Research to text files in ./Research_txt.

- Converts each PDF that has no text file yet. Pass --all to convert every PDF again.
- Never deletes anything: a text file whose PDF has gone is left in place.
- Creates ./Research_txt if it doesn't exist.
- Keeps base filenames the same, but with .txt extension.
"""

import re
import sys
from pathlib import Path
from PyPDF2 import PdfReader

# Directory paths relative to the script location
BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "Research"
TXT_DIR = BASE_DIR / "Research_txt"


def convert_pdf_to_txt(pdf_path: Path) -> str:
    """Extract text from a PDF file and collapse runs of whitespace."""
    reader = PdfReader(str(pdf_path))
    text_chunks = [page.extract_text() or "" for page in reader.pages]
    raw_text = "\n".join(text_chunks)
    # Collapse any run of whitespace (spaces, tabs, newlines) to a single space
    cleaned_text = re.sub(r"\s+", " ", raw_text).strip()
    return cleaned_text


def main() -> None:
    if not PDF_DIR.exists():
        print(f"PDF source directory '{PDF_DIR}' does not exist.")
        return

    TXT_DIR.mkdir(parents=True, exist_ok=True)
    redo_all = "--all" in sys.argv[1:]

    for pdf_file in sorted(PDF_DIR.glob("*.pdf")):
        txt_filename = TXT_DIR / (pdf_file.stem + ".txt")
        if txt_filename.exists() and not redo_all:
            continue
        print(f"Converting {pdf_file.name} -> {txt_filename.name}")
        try:
            text = convert_pdf_to_txt(pdf_file)
            with txt_filename.open("w", encoding="utf-8") as f:
                f.write(text)
        except Exception as exc:
            print(f"Failed to convert {pdf_file.name}: {exc}")


if __name__ == "__main__":
    main()
