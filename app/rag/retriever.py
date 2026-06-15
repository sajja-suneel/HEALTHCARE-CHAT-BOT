from qdrant_client import QdrantClient
from app.rag.embedding import get_embedding
from app.config.settings import (
    COLLECTION_NAME,
    QDRANT_URL,
    QDRANT_API_KEY,
    SCORE_THRESHOLD,
    TOP_K,
)
from app.rag.log import logger

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


def retrieve_context(
    question,
    TOP_K=TOP_K,
    score_threshold=SCORE_THRESHOLD
):
    """
    Retrieves relevant document chunks from Qdrant based on the user's question,
    limiting the results to TOP_K and filtering by score_threshold.
    """
    logger.info(f"User Query: {question}")
    query_embedding = get_embedding(question)
    logger.info("Searching Qdrant...")
    try:
        # Query Qdrant passing both TOP_K (limit) and score_threshold
        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=TOP_K,
            score_threshold=score_threshold
        )
        results = search_result.points
        logger.info(
            f"Retrieved {len(results)} search results"
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

    retrieved_docs = []
    for result in results:
        score = getattr(
            result,
            "score",
            0.0
        )
        # Apply threshold check locally as a safety measure
        if score < score_threshold:
            continue
        
        if result.payload:
            # Extract 'page' and 'source' from top-level payload or nested 'metadata' dictionary
            payload_metadata = result.payload.get("metadata", {})
            if not isinstance(payload_metadata, dict):
                payload_metadata = {}

            page = result.payload.get("page") or payload_metadata.get("page") or "Unknown"
            source = result.payload.get("source") or payload_metadata.get("source") or "Unknown"

            retrieved_docs.append(
                {
                    "text": result.payload.get(
                        "text",
                        ""
                    ),
                    "page": page,
                    "source": source,
                    "score": round(score, 4)
                }
            )

    logger.info(
        f"Retrieved {len(retrieved_docs)} chunks after threshold filtering"
    )
    return retrieved_docs