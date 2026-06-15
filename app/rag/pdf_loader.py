import os
import fitz
import pandas as pd

from docx import Document

from .log import logger
from app.rag.ocr import ocr_pdf_page


def extract_text_from_pdf(file_path):
    doc = None
    try:
        doc = fitz.open(file_path)
        pages = []

        for page in doc:
            page_text = ""
            try:
                # Try normal text extraction first
                text = page.get_text("text")

                if text and text.strip():
                    page_text = text
                else:
                    logger.info(
                        f"OCR running on page {page.number + 1}"
                    )
                    ocr_text = ocr_pdf_page(page)
                    page_text = ocr_text

                if page_text.strip():
                    pages.append({
                        "text": page_text.strip(),
                        "page": page.number + 1
                    })

            except Exception as page_error:
                logger.error(
                    f"Error processing page "
                    f"{page.number + 1}: "
                    f"{page_error}"
                )

        return pages

    except Exception as e:
        logger.error(
            f"PDF processing failed: {e}"
        )
        raise

    finally:
        if doc:
            doc.close()


def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        return "\n".join(
            para.text
            for para in doc.paragraphs
        )
    except Exception as e:
        logger.error(
            f"DOCX processing failed: {e}"
        )
        raise


def extract_text_from_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        return df.to_string(
            index=False
        )
    except Exception as e:
        logger.error(
            f"CSV processing failed: {e}"
        )
        raise


def extract_text_from_excel(file_path):
    try:
        df = pd.read_excel(file_path)
        return df.to_string(
            index=False
        )
    except Exception as e:
        logger.error(
            f"Excel processing failed: {e}"
        )
        raise


def extract_text_from_txt(file_path):
    try:
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:
            return f.read()
    except Exception as e:
        logger.error(
            f"TXT processing failed: {e}"
        )
        raise


def process_document(file_path):
    ext = os.path.splitext(
        file_path
    )[1].lower()

    if ext == ".pdf":
        logger.info(
            f"Processing PDF: {file_path}"
        )
        return extract_text_from_pdf(
            file_path
        )

    elif ext == ".docx":
        logger.info(
            f"Processing DOCX: {file_path}"
        )
        text = extract_text_from_docx(file_path)
        return [{"text": text, "page": 1}]

    elif ext == ".csv":
        logger.info(
            f"Processing CSV: {file_path}"
        )
        text = extract_text_from_csv(file_path)
        return [{"text": text, "page": 1}]

    elif ext in [".xlsx", ".xls"]:
        logger.info(
            f"Processing Excel: {file_path}"
        )
        text = extract_text_from_excel(file_path)
        return [{"text": text, "page": 1}]

    elif ext == ".txt":
        logger.info(
            f"Processing TXT: {file_path}"
        )
        text = extract_text_from_txt(file_path)
        return [{"text": text, "page": 1}]

    else:
        raise ValueError(
            f"Unsupported file type: {ext}"
        )


def load_all_documents(
    folder_path="data/pdfs"
):
    documents = []

    if not os.path.exists(
        folder_path
    ):
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    for file in os.listdir(
        folder_path
    ):
        file_path = os.path.join(
            folder_path,
            file
        )

        if not os.path.isfile(
            file_path
        ):
            continue

        try:
            pages = process_document(
                file_path
            )

            # Keep track of individual page metadata
            for p in pages:
                documents.append(
                    {
                        "source": file,
                        "text": p["text"],
                        "page": p["page"]
                    }
                )

            logger.info(
                f"Successfully processed: {file} ({len(pages)} pages)"
            )

        except Exception as e:
            logger.error(
                f"Failed processing "
                f"{file}: {e}"
            )

    return documents


if __name__ == "__main__":
    docs = load_all_documents(
        "data/pdfs"
    )

    print(
        f"Total Document Pages: {len(docs)}"
    )

    if docs:
        print(
            f"\nSource: "
            f"{docs[0]['source']} | Page: {docs[0]['page']}"
        )

        print(
            "\nContent Preview:\n"
        )

        print(
            docs[0]["text"][:1000]
        )