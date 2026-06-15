from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "healthcare_docs"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "all-MiniLM-L6-v2"
)

TOP_K = 3
SCORE_THRESHOLD = 0.40