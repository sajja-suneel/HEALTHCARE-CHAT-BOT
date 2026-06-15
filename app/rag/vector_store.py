import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct
)

from app.config.settings import (
    QDRANT_URL,
    QDRANT_API_KEY,
    COLLECTION_NAME
)

from .embedding import get_embedding
from .text_splitter import split_documents
from .log import logger


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=300
)


def create_collection():

    collections = client.get_collections()

    existing = [
        c.name
        for c in collections.collections
    ]

    if COLLECTION_NAME in existing:

        logger.info(
            f"{COLLECTION_NAME} already exists"
        )

        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

    logger.info(
        f"{COLLECTION_NAME} created"
    )


# New function to get currently indexed filenames
def get_indexed_sources():
    """Fetches unique sources (filenames) already indexed in Qdrant."""
    try:
        collections = client.get_collections()
        existing = [c.name for c in collections.collections]
        if COLLECTION_NAME not in existing:
            return set()

        sources = set()
        offset = None
        # Scroll through the collection to collect all unique sources
        while True:
            response, offset = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=100,
                with_payload=True,
                with_vectors=False,
                offset=offset
            )
            for point in response:
                if point.payload and "source" in point.payload:
                    sources.add(point.payload["source"])
            if offset is None:
                break
        return sources
    except Exception as e:
        logger.error(f"Error fetching indexed sources: {e}")
        return set()


def store_vectors():

    create_collection()

    # Get the list of already indexed files to skip them
    skip_sources = get_indexed_sources()
    if skip_sources:
        logger.info(f"Already indexed files: {skip_sources}")

    # Pass the skip list to the document splitter
    chunks = split_documents(skip_sources=skip_sources)

    if not chunks:

        logger.warning(
            "No chunks found (or all files are already indexed)"
        )

        return

    logger.info(
        "Generating Embeddings"
    )

    points = []

    for chunk in chunks:

        try:

            embedding = get_embedding(
                chunk["text"]  
            )

            # Store text, source, and page metadata in Qdrant payload
            points.append(  
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "page": chunk.get("page", "Unknown")
                    }
                )
            )

        except Exception as e:

            logger.error(
                f"Embedding Error: {e}"
            )

    logger.info(
        f"Generated {len(points)} vectors"
    )

    if not points:

        logger.warning(
            "No vectors generated"
        )

        return

    batch_size = 10

    logger.info(
        "Uploading vectors to Qdrant"
    )

    for i in range(
        0,
        len(points),
        batch_size
    ):

        batch = points[
            i:i + batch_size
        ]

        try:

            client.upsert(
                collection_name=COLLECTION_NAME,
                points=batch,
                wait=True
            )

            logger.info(
                f"Uploaded Batch "
                f"{i // batch_size + 1}"
            )

        except Exception as e:

            logger.error(
                f"Batch Upload Error: {e}"
            )

    logger.info(
        "Vector Storage Completed"
    )


if __name__ == "__main__":

    try:

        store_vectors()

    except Exception as e:

        logger.error(
            f"Vector Store Error: {e}"
        )

        print(
            f"\nERROR: {e}"
        )