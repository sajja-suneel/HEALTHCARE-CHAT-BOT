"""
Run PDF loading with smart OCR from the backend folder:

    python run_ocr.py
    python run_ocr.py data/pdfs/your_file.pdf
"""

import sys

from app.rag.pdf_loader import (
    load_all_documents,
    process_document,
)


def main():

    if len(sys.argv) > 1:

        file_path = sys.argv[1]

        text = process_document(file_path)

        print(f"Characters: {len(text)}")
        print("\nPreview:\n")
        print(text[:1000])

        return

    docs = load_all_documents("data/pdfs")

    print(f"Total Documents: {len(docs)}")

    if docs:

        print(f"\nSource: {docs[0]['source']}")
        print("\nContent Preview:\n")
        print(docs[0]["text"][:1000])


if __name__ == "__main__":
    main()
