# Script to batch convert all PDFs in the current directory to text files
# using PyPDF2. Each PDF will produce a .txt file with the same base name.

import os
from PyPDF2 import PdfReader


def convert_pdf_to_txt(pdf_path: str) -> str:
    """Extract text from a PDF file and return it."""
    reader = PdfReader(pdf_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or "")
    return "\n".join(text)


def main():
    # Find all PDF files in the current directory
    for entry in os.listdir('.'):  # same directory as script
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
