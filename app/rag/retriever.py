from qdrant_client import QdrantClient
from qdrant_client.models import Prefetch, FusionQuery, Fusion, SparseVector
from app.rag.embedding import get_dense_embedding, get_sparse_embedding
from app.config.settings import (
    COLLECTION_NAME,
    QDRANT_URL,
    QDRANT_API_KEY,
    
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
    
):
    """
    Retrieves relevant document chunks from Qdrant using Hybrid Search
    (combining dense semantics and sparse keywords using RRF).
    """
    logger.info(f"User Query: {question}")
    dense_embedding = get_dense_embedding(question)
    sparse_emb = get_sparse_embedding(question)
    
    logger.info("Searching Qdrant using Hybrid Search (RRF)...")
    try:
        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=[
                # Sub-query 1: Dense Semantic Search
                Prefetch(
                    query=dense_embedding,
                    using="dense",
                    limit=TOP_K
                ),
                # Sub-query 2: Sparse Keyword Search
                Prefetch(
                    query=SparseVector(
                        indices=sparse_emb["indices"],
                        values=sparse_emb["values"]
                    ),
                    using="sparse",
                    limit=TOP_K
                )
            ],
            # Combine the rankings from both queries using Reciprocal Rank Fusion (RRF)
            query=FusionQuery(fusion=Fusion.RRF),
            limit=TOP_K
        )
        results = search_result.points
        logger.info(
            f"Retrieved {len(results)} hybrid search results"
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
        # Note: Bypassing score threshold check because Hybrid Search uses RRF,
        # which produces rank-based scores that do not correspond to standard Cosine similarity thresholds.
        if result.payload:
            payload_metadata = result.payload.get("metadata", {})
            if not isinstance(payload_metadata, dict):
                payload_metadata = {}

            page = result.payload.get("page") or payload_metadata.get("page") or "Unknown"
            source = result.payload.get("source") or payload_metadata.get("source") or "Unknown"

            retrieved_docs.append(
                {
                    "text": result.payload.get("text", ""),
                    "page": page,
                    "source": source,
                    "score": round(score, 4)
                }
            )

    logger.info(
        f"Retrieved {len(retrieved_docs)} chunks after RRF filtering"
    )
    return retrieved_docs