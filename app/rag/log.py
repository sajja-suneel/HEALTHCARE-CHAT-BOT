import os
import logging
from logging.handlers import RotatingFileHandler

# =====================================================
# Create Logs Directory
# =====================================================

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    "healthcare_rag.log"
)

# =====================================================
# Logger Configuration
# =====================================================

logger = logging.getLogger("HealthcareRAG")
logger.setLevel(logging.INFO)

if not logger.handlers:

    formatter = logging.Formatter(
        "[%(asctime)s] "
        "[%(levelname)s] "
        "[%(filename)s:%(lineno)d] "
        "%(message)s"
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
        encoding="utf-8"
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# =====================================================
# RAG Logging Helper Functions
# =====================================================

def log_document_received(file_name, file_path):
    logger.info("=" * 60)
    logger.info("DOCUMENT RECEIVED")
    logger.info(f"File Name: {file_name}")
    logger.info(f"File Path: {file_path}")
    logger.info("=" * 60)


def log_pdf_extraction_started():
    logger.info("STARTING PDF EXTRACTION")


def log_pdf_extraction_completed(text):
    logger.info("PDF EXTRACTION COMPLETED")
    logger.info(f"Characters Extracted: {len(text)}")


def log_ocr_started():
    logger.info("NO TEXT FOUND IN PDF")
    logger.info("STARTING OCR")


def log_ocr_completed(text):
    logger.info("OCR COMPLETED")
    logger.info(f"OCR Characters Extracted: {len(text)}")


def log_chunking_started(chunk_size, chunk_overlap):
    logger.info("STARTING TEXT SPLITTING")
    logger.info(f"Chunk Size: {chunk_size}")
    logger.info(f"Chunk Overlap: {chunk_overlap}")


def log_chunking_completed(chunks):
    logger.info("TEXT SPLITTING COMPLETED")
    logger.info(f"Total Chunks Created: {len(chunks)}")


def log_embeddings_started():
    logger.info("GENERATING EMBEDDINGS")


def log_embeddings_completed(count):
    logger.info(f"EMBEDDINGS GENERATED: {count}")


def log_qdrant_upload_started(collection_name, points_count):
    logger.info("UPLOADING TO QDRANT")
    logger.info(f"Collection Name: {collection_name}")
    logger.info(f"Points Count: {points_count}")


def log_qdrant_upload_completed():
    logger.info("QDRANT UPSERT SUCCESSFUL")


def log_retrieval_started(query):
    logger.info("=" * 60)
    logger.info("QUESTION RECEIVED")
    logger.info(query)
    logger.info("=" * 60)

    logger.info("RETRIEVING CONTEXT")
    logger.info(f"User Query: {query}")


def log_qdrant_search_started():
    logger.info("SEARCHING QDRANT")


def log_qdrant_search_completed(results_count):
    logger.info(f"Retrieved {results_count} Search Results")


def log_chunks_after_filter(count):
    logger.info(
        f"Retrieved {count} Chunks After Threshold Filtering"
    )


def log_detected_intent(intent):
    logger.info(f"Intent: {intent}")


def log_llm_request():
    logger.info("SENDING TO GEMINI")


def log_llm_response():
    logger.info("RESPONSE GENERATED")


def log_processing_time(seconds):
    logger.info(
        f"TOTAL PROCESSING TIME: {seconds:.2f} sec"
    )


def log_error(message):
    logger.exception(message)