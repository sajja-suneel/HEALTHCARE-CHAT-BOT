import os
import pandas as pd
from docx import Document
from .pdf_loader import extract_text_from_pdf
from .log import logger
def load_file(file_path):
    ext = os.path.splitext(
        file_path
    )[1].lower()

    try:
        logger.info(
            f"Loading: {file_path}"
        )

        if ext == ".pdf":
            pages = extract_text_from_pdf(
                file_path
            )
            if isinstance(pages, str):
                return [{"text": pages, "page": 1}]
            return pages

        elif ext == ".csv":
            df = pd.read_csv(
                file_path
            )
            text = df.to_string(
                index=False
            )
            return [{"text": text, "page": 1}]

        elif ext in [
            ".xlsx",
            ".xls"
        ]:
            df = pd.read_excel(
                file_path
            )
            text = df.to_string(
                index=False
            )
            return [{"text": text, "page": 1}]

        elif ext == ".docx":
            doc = Document(
                file_path
            )
            text = "\n".join(
                para.text
                for para in doc.paragraphs
            )
            return [{"text": text, "page": 1}]

        elif ext == ".txt":
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:
                text = f.read()
            return [{"text": text, "page": 1}]

        else:
            logger.warning(
                f"Unsupported File: {file_path}"
            )
            return []

    except Exception as e:
        logger.error(
            f"Error Loading {file_path}: {e}"
        )
        return []
def recursive_split_text(
    text,
    chunk_size=1000,
    chunk_overlap=100
):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (
            chunk_size
            - chunk_overlap
        )

    return chunks
# Updated split_documents to accept and check skip_sources
def split_documents(skip_sources=None):
    if skip_sources is None:
        skip_sources = set()
        
    data_folder = "data"
    all_chunks = []

    logger.info(
        "Document Splitting Started"
    )

    if not os.path.exists(
        data_folder
    ):
        logger.error(
            f"{data_folder} not found"
        )
        return []

    for root, dirs, files in os.walk(
        data_folder
    ):
        for file in files:
            # Check if this file is already present in Qdrant
            if file in skip_sources:
                logger.info(
                    f"File '{file}' is already indexed in Qdrant. Skipping."
                )
                continue

            file_path = os.path.join(
                root,
                file
            )

            logger.info(
                f"Processing: {file_path}"
            )

            pages = load_file(
                file_path
            )

            if not pages:
                logger.warning(
                    f"No Text Found: {file}"
                )
                continue

            for p in pages:
                page_text = p["text"]
                page_no = p["page"]

                chunks = recursive_split_text(
                    text=page_text,
                    chunk_size=1000,
                    chunk_overlap=100
                )

                logger.info(
                    f"{file} (Page {page_no}) -> {len(chunks)} chunks"
                )

                for chunk in chunks:
                    all_chunks.append(
                        {
                            "text": chunk,
                            "source": file,
                            "page": page_no
                        }
                    )

    logger.info(
        f"Total Chunks: {len(all_chunks)}"
    )

    return all_chunks

if __name__ == "__main__":
    chunks = split_documents()

    print("\n")
    print("=" * 50)
    print("TOTAL CHUNKS")
    print("=" * 50)

    print(
        len(chunks)
    )

    if chunks:
        print("\n")
        print("=" * 50)
        print("FIRST CHUNK")
        print("=" * 50)

        print(
            chunks[0]["text"][:500]
        )

        print("\nSOURCE:")
        print(
            f"{chunks[0]['source']} | Page: {chunks[0].get('page')}"
        )

    else:
        print(
            "\nNo Chunks Created"
        )
        print(
            "Check OCR Output or File Location"
        )