import os
import fitz
import pandas as pd
import pytesseract

from pypdf import PdfReader
from docx import Document
from PIL import Image

from .log import logger


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def ocr_pdf_page(page):
    pix = page.get_pixmap(
        matrix=fitz.Matrix(3, 3)
    )

    img = Image.frombytes(
        "RGB",
        [pix.width, pix.height],
        pix.samples
    )

    return pytesseract.image_to_string(
        img,
        lang="eng",
        config="--psm 6"
    )


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    pages = []

    for index, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            pages.append({
                "text": page_text.strip(),
                "page": index + 1
            })

    return pages


def extract_text_from_scanned_pdf(file_path):
    doc = fitz.open(file_path)
    pages = []

    try:
        for page in doc:
            logger.info(
                f"OCR running on page {page.number + 1}"
            )
            ocr_text = ocr_pdf_page(page)
            if ocr_text and ocr_text.strip():
                pages.append({
                    "text": ocr_text.strip(),
                    "page": page.number + 1
                })
        return pages

    finally:
        doc.close()


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join(
        para.text
        for para in doc.paragraphs
    )


def extract_text_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_string(index=False)


def extract_text_from_excel(file_path):
    df = pd.read_excel(file_path)
    return df.to_string(index=False)


def extract_text_from_txt(file_path):
    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


def process_document(file_path):
    ext = os.path.splitext(
        file_path
    )[1].lower()

    if ext == ".pdf":
        logger.info(
            f"Processing PDF: {file_path}"
        )
        pages = extract_text_from_pdf(
            file_path
        )

        if not pages:
            logger.info(
                "No text found. Running OCR..."
            )
            pages = extract_text_from_scanned_pdf(
                file_path
            )
        return pages

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

    for file in os.listdir(folder_path):
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

            for p in pages:
                documents.append(
                    {
                        "source": file,
                        "text": p["text"],
                        "page": p["page"]
                    }
                )

            logger.info(
                f"Processed {file} ({len(pages)} pages)"
            )

        except Exception as e:
            logger.error(
                f"Failed {file}: {e}"
            )

    return documents