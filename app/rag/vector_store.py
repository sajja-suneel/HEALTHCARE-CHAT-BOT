import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVectorParams,
    SparseVector
)

from app.config.settings import (
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME
)

from .embedding import get_dense_embedding, get_sparse_embedding
from .text_splitter import split_documents
from .log import logger


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=300
)


def create_collection():
    collections = client.get_collections()
    existing = [c.name for c in collections.collections]

    if COLLECTION_NAME in existing:
        logger.info(f"{COLLECTION_NAME} already exists")
        return

    # Create the collection with both dense and sparse configurations
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams()
        }
    )
    logger.info(f"{COLLECTION_NAME} created for Hybrid Search")


def get_indexed_hashes():
    """Fetches unique file hashes already indexed in Qdrant."""
    try:
        collections = client.get_collections()
        existing = [c.name for c in collections.collections]
        if COLLECTION_NAME not in existing:
            return set()

        hashes = set()
        offset = None
        while True:
            response, offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            for point in response:
                if point.payload and "file_hash" in point.payload:
                    hashes.add(point.payload["file_hash"])
            if offset is None:
                break
        return hashes
    except Exception as e:
        logger.error(f"Error fetching indexed hashes: {e}")
        return set()


def store_vectors():
    create_collection()

    skip_hashes = get_indexed_hashes()
    if skip_hashes:
        logger.info(f"Already indexed file hashes count: {len(skip_hashes)}")

    chunks = split_documents(skip_hashes=skip_hashes)

    if not chunks:
        logger.warning("No chunks found")
        return

    logger.info("Generating Embeddings")
    points = []

    for chunk in chunks:
        try:
            # Generate both dense and sparse representations
            dense_embedding = get_dense_embedding(chunk["text"])
            sparse_emb = get_sparse_embedding(chunk["text"])

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    # Pass a dictionary for multiple named vectors
                    vector={
                        "dense": dense_embedding,
                        "sparse": SparseVector(
                            indices=sparse_emb["indices"],
                            values=sparse_emb["values"]
                        )
                    },
                    payload={
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "page": chunk.get("page", "Unknown"),
                        "file_hash": chunk.get("file_hash")
                    }
                )
            )

        except Exception as e:
            logger.error(f"Embedding Error: {e}")

    logger.info(f"Generated {len(points)} vectors")

    if not points:
        logger.warning("No vectors generated")
        return

    batch_size = 10
    logger.info("Uploading vectors to Qdrant")

    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True
            )
            logger.info(f"Uploaded Batch {i // batch_size + 1}")
        except Exception as e:
            logger.error(f"Batch Upload Error: {e}")

    logger.info("Vector Storage Completed")


if __name__ == "__main__":
    try:
        store_vectors()
    except Exception as e:
        logger.error(f"Vector Store Error: {e}")
        print(f"\nERROR: {e}")