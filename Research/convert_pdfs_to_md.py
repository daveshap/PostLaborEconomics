"""Batch convert PDFs in the current directory to Markdown files.

This script extracts text from each PDF and saves it as a Markdown file in
`../docs/research/`. The output directory is created if it does not already
exist. Each generated Markdown file begins with a heading derived from the
original PDF filename.
"""

import os
from PyPDF2 import PdfReader


def convert_pdf_to_markdown(pdf_path: str, output_dir: str) -> None:
    """Extract text from `pdf_path` and write it to a Markdown file."""
    reader = PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        text_chunks.append(page.extract_text() or "")

    raw_text = "\n\n".join(text_chunks)
    title = os.path.splitext(os.path.basename(pdf_path))[0]
    md_content = f"# {title}\n\n{raw_text}\n"

    os.makedirs(output_dir, exist_ok=True)
    md_path = os.path.join(output_dir, f"{title}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)


def main() -> None:
    output_dir = os.path.join("..", "docs", "research")
    for entry in os.listdir('.'):
        if entry.lower().endswith('.pdf') and os.path.isfile(entry):
            print(f"Converting {entry} -> {output_dir}")
            try:
                convert_pdf_to_markdown(entry, output_dir)
            except Exception as e:
                print(f"Failed to convert {entry}: {e}")


if __name__ == "__main__":
    main()
