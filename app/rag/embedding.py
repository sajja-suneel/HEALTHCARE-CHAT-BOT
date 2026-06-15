# rag/embedding.py

from sentence_transformers import SentenceTransformer

from .log import logger

logger.info("Loading Embedding Model")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

logger.info("Embedding Model Loaded")


def get_embedding(text):

    return model.encode(
        text
    ).tolist()