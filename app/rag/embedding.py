from sentence_transformers import SentenceTransformer
from fastembed import SparseTextEmbedding

# Initialize the embedding models
dense_model = SentenceTransformer("all-MiniLM-L6-v2")
# SPLADE is a highly effective model for keyword / sparse embeddings
sparse_model = SparseTextEmbedding("prithivida/Splade_PP_en_v1")


def get_dense_embedding(text: str):
    """
    Generates a 384-dimensional dense vector embedding for the input text.
    """
    if not text:
        return [0.0] * 384
    return dense_model.encode(text).tolist()


def get_sparse_embedding(text: str):
    """
    Generates a sparse vector embedding for the input text using SPLADE.
    """
    if not text:
        return {"indices": [], "values": []}
    # Fastembed returns a generator of SparseEmbedding objects
    embeddings = list(sparse_model.embed([text]))
    sparse_emb = embeddings[0]
    return {
        "indices": sparse_emb.indices.tolist(),
        "values": sparse_emb.values.tolist()
    }