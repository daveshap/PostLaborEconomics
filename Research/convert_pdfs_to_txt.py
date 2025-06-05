# Script to batch convert all PDFs in the current directory to text files
# using PyPDF2. Each PDF will produce a .txt file with the same base name.

import os
import re
from PyPDF2 import PdfReader


def convert_pdf_to_txt(pdf_path: str) -> str:
    """Extract text from a PDF file, collapse whitespace, and return it."""
    reader = PdfReader(pdf_path)
    text_chunks = []
    for page in reader.pages:
        text_chunks.append(page.extract_text() or "")
    raw_text = "\n".join(text_chunks)
    # Collapse any run of whitespace (spaces, tabs, newlines) to a single space
    cleaned_text = re.sub(r"\s+", " ", raw_text).strip()
    return cleaned_text


def main():
    # Find all PDF files in the current directory
    for entry in os.listdir('.'):
        if entry.lower().endswith('.pdf') and os.path.isfile(entry):
            txt_filename = os.path.splitext(entry)[0] + '.txt'
            print(f"Converting {entry} -> {txt_filename}")
            try:
                pdf_text = convert_pdf_to_txt(entry)
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(pdf_text)
            except Exception as e:
                print(f"Failed to convert {entry}: {e}")


if __name__ == '__main__':
    main()
