#!/usr/bin/env python3
"""
Batch convert all PDFs in ./Research to text files in ./Research_txt.

- Clears (deletes) existing contents of ./Research_txt at start.
- Creates ./Research_txt if it doesn't exist.
- Keeps base filenames the same, but with .txt extension.
"""

import re
import shutil
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


def prepare_output_dir() -> None:
    """Ensure TXT_DIR exists and is empty."""
    if TXT_DIR.exists():
        # Remove everything inside the directory
        for item in TXT_DIR.iterdir():
            if item.is_file() or item.is_symlink():
                item.unlink(missing_ok=True)
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
    else:
        TXT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    if not PDF_DIR.exists():
        print(f"PDF source directory '{PDF_DIR}' does not exist.")
        return

    prepare_output_dir()

    for pdf_file in PDF_DIR.glob("*.pdf"):
        txt_filename = TXT_DIR / (pdf_file.stem + ".txt")
        print(f"Converting {pdf_file.name} -> {txt_filename.name}")
        try:
            text = convert_pdf_to_txt(pdf_file)
            with txt_filename.open("w", encoding="utf-8") as f:
                f.write(text)
        except Exception as exc:
            print(f"Failed to convert {pdf_file.name}: {exc}")


if __name__ == "__main__":
    main()
