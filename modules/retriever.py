"""
modules/retriever.py
Module 3: FAISS Vector Index & Passage Retrieval

This module is responsible for:
1. Indexing chunk embeddings into an in-memory FAISS vector index (IndexFlatIP).
2. Maintaining strict association between vector positions and original chunk metadata.
3. Querying the FAISS index with a vectorized query string.
4. Returning the top-k most relevant text chunks with source page numbers and cosine similarity scores.
5. Providing robust validation for empty indexes, invalid queries, and out-of-range top-k values.

Similarity Metric Note:
With L2-normalized embedding vectors, FAISS IndexFlatIP (Inner Product) computes exact
cosine similarity:
    score = (q . d) / (||q|| * ||d||) = cos(theta)
Higher scores indicate greater semantic similarity, ranging from -1.0 to 1.0 (with 1.0
denoting identical semantic direction).
"""

import logging
from typing import Any, Dict, List, Optional, Union
import faiss
import numpy as np

from modules.embeddings import (
    DEFAULT_MODEL_NAME,
    generate_embeddings,
    generate_query_embedding,
    get_embedding_dimension,
)

logger = logging.getLogger(__name__)


class VectorRetriever:
    """
    A lightweight, in-memory FAISS vector retriever that pairs a FAISS IndexFlatIP
    with the original chunk records and metadata produced by Module 2.
    """

    def __init__(
        self,
        index: Optional[faiss.Index],
        chunks: List[Dict],
        model_name: str = DEFAULT_MODEL_NAME,
        dimension: Optional[int] = None,
        device: str = "cpu",
    ):
        """
        Initializes the VectorRetriever.

        Parameters:
            index (faiss.Index or None): Initialized FAISS index.
            chunks (List[Dict]): Ordered list of chunk dictionaries corresponding to index vectors.
            model_name (str): SentenceTransformers model used for indexing.
            dimension (int or None): Dimensionality of the vectors.
            device (str): Device for inference.
        """
        self.index = index
        self.chunks = list(chunks) if chunks else []
        self.model_name = model_name
        self.device = device

        if dimension is not None:
            self.dimension = dimension
        elif index is not None and hasattr(index, "d"):
            self.dimension = index.d
        else:
            try:
                self.dimension = get_embedding_dimension(model_name=model_name, device=device)
            except Exception:
                self.dimension = 384

    @property
    def total_chunks(self) -> int:
        """Returns the number of indexed chunks."""
        return len(self.chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        model_instance: Optional[object] = None,
    ) -> List[Dict]:
        """
        Retrieves the top-k most relevant chunks for a user search query.

        Parameters:
            query (str): The search query text.
            top_k (int): Number of passages to retrieve (default: 3).
            model_instance: Optional pre-loaded or mock model for query encoding.

        Returns:
            List[Dict]: List of retrieved chunk dictionaries sorted by descending similarity score.
                        Each dict contains:
                            - chunk_id (str)
                            - text (str)
                            - source (str)
                            - page_number (int)
                            - score (float) [cosine similarity]
                            - char_count (int, optional)
                            - word_count (int, optional)

        Raises:
            ValueError: If query is empty/whitespace or top_k is not a positive integer.
            TypeError: If query is not a string.
        """
        # Validate query
        if query is None or not isinstance(query, str):
            raise TypeError(f"Query must be a string, got: {type(query).__name__}")

        stripped_query = query.strip()
        if not stripped_query:
            raise ValueError("Query cannot be empty or whitespace-only.")

        # Validate top_k
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got: {top_k}")

        # If index is empty or has no vectors, return empty list
        if self.index is None or self.index.ntotal == 0 or len(self.chunks) == 0:
            return []

        # Encode query to normalized float32 vector
        query_vec = generate_query_embedding(
            query=stripped_query,
            model_name=self.model_name,
            normalize=True,
            device=self.device,
            model_instance=model_instance,
        )

        # Validate query dimension matches index dimension
        if query_vec.shape[1] != self.dimension:
            raise ValueError(
                f"Query embedding dimension ({query_vec.shape[1]}) does not match "
                f"index dimension ({self.dimension})."
            )

        # Limit search k to available vectors in the index
        k_to_search = min(top_k, self.index.ntotal)
        if k_to_search == 0:
            return []

        # Execute FAISS search
        raw_scores, raw_indices = self.index.search(query_vec, k_to_search)

        results: List[Dict] = []
        seen_chunk_ids = set()

        # Parse retrieved items
        for score, idx in zip(raw_scores[0], raw_indices[0]):
            # FAISS returns -1 for unoccupied result slots
            if idx == -1 or idx >= len(self.chunks):
                continue

            chunk = self.chunks[idx]
            chunk_id = chunk.get("chunk_id", f"chunk_{idx + 1}")

            # Avoid duplicate chunks
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)

            result_item = {
                "chunk_id": chunk_id,
                "text": chunk.get("text", ""),
                "source": chunk.get("source", "document.pdf"),
                "page_number": chunk.get("page_number", 1),
                "score": round(float(score), 4),
            }

            if "char_count" in chunk:
                result_item["char_count"] = chunk["char_count"]
            if "word_count" in chunk:
                result_item["word_count"] = chunk["word_count"]

            results.append(result_item)

        return results


def build_faiss_index(
    chunks: List[Dict],
    embeddings: Optional[np.ndarray] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = "cpu",
    model_instance: Optional[object] = None,
) -> VectorRetriever:
    """
    Builds an in-memory FAISS vector index from chunk records.

    Parameters:
        chunks (List[Dict]): List of chunk dictionaries produced by Module 2.
        embeddings (np.ndarray, optional): Precomputed 2D float32 array of embeddings.
                                           If None, generated automatically using Module 3 embeddings.
        model_name (str): Name of the SentenceTransformers embedding model.
        device (str): Inference device ("cpu").
        model_instance: Optional model instance for testing or dependency injection.

    Returns:
        VectorRetriever: A retriever instance binding the FAISS index and the source chunk records.
    """
    if not chunks:
        # Return an empty retriever instance for empty document chunks
        dim = 384
        try:
            if embeddings is not None and embeddings.ndim == 2 and embeddings.shape[1] > 0:
                dim = embeddings.shape[1]
            elif model_instance is not None and hasattr(model_instance, "get_sentence_embedding_dimension"):
                dim = model_instance.get_sentence_embedding_dimension()
            else:
                dim = get_embedding_dimension(model_name=model_name, device=device)
        except Exception:
            dim = 384

        empty_index = faiss.IndexFlatIP(dim)
        return VectorRetriever(index=empty_index, chunks=[], model_name=model_name, dimension=dim, device=device)

    # Compute embeddings if not provided
    if embeddings is None:
        embeddings = generate_embeddings(
            chunks=chunks,
            model_name=model_name,
            batch_size=32,
            normalize=True,
            device=device,
            model_instance=model_instance,
        )

    embeddings = np.asarray(embeddings, dtype=np.float32)

    if embeddings.shape[0] != len(chunks):
        raise ValueError(
            f"Embedding count ({embeddings.shape[0]}) does not match chunk count ({len(chunks)})."
        )

    dimension = embeddings.shape[1]

    # Create inner product index (equivalent to cosine similarity for normalized vectors)
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    return VectorRetriever(
        index=index,
        chunks=chunks,
        model_name=model_name,
        dimension=dimension,
        device=device,
    )


def retrieve_relevant_chunks(
    query: str,
    retriever_or_index: Union[VectorRetriever, Dict[str, Any], Any],
    top_k: int = 3,
    chunks: Optional[List[Dict]] = None,
    model_name: str = DEFAULT_MODEL_NAME,
    model_instance: Optional[object] = None,
) -> List[Dict]:
    """
    Retrieves top-k relevant chunks using either a VectorRetriever instance,
    a dictionary containing {'index': faiss.Index, 'chunks': list}, or an index with chunks.

    Parameters:
        query (str): The search query.
        retriever_or_index: A VectorRetriever, a dict, or raw faiss.Index.
        top_k (int): Number of passages to return.
        chunks (List[Dict], optional): Required only if a raw faiss.Index is passed.
        model_name (str): Embedding model identifier.
        model_instance: Optional pre-loaded or mock model.

    Returns:
        List[Dict]: The top-k retrieved chunks with preserved metadata and similarity scores.
    """
    if isinstance(retriever_or_index, VectorRetriever):
        return retriever_or_index.retrieve(query=query, top_k=top_k, model_instance=model_instance)

    if isinstance(retriever_or_index, dict):
        idx = retriever_or_index.get("index")
        chk = retriever_or_index.get("chunks", [])
        m_name = retriever_or_index.get("model_name", model_name)
        retriever = VectorRetriever(index=idx, chunks=chk, model_name=m_name)
        return retriever.retrieve(query=query, top_k=top_k, model_instance=model_instance)

    if hasattr(retriever_or_index, "search"):
        # Raw FAISS index passed
        chk = chunks if chunks is not None else []
        retriever = VectorRetriever(index=retriever_or_index, chunks=chk, model_name=model_name)
        return retriever.retrieve(query=query, top_k=top_k, model_instance=model_instance)

    raise TypeError(
        f"Expected VectorRetriever, dict, or faiss.Index, got: {type(retriever_or_index).__name__}"
    )
