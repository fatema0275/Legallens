"""
modules/embeddings.py
Module 3: Embedding Generation

This module is responsible for:
1. Loading and caching the Sentence Transformers model (default: all-MiniLM-L6-v2).
2. Converting document text chunks into numerical dense vector embeddings.
3. Encoding user search queries into single query vector embeddings.
4. Normalizing embeddings (L2 norm) for cosine similarity computation with FAISS IndexFlatIP.
5. Providing CPU-first inference for compatibility with standard student laptops.
"""

import logging
from typing import Dict, List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

# Default model configuration
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DEVICE = "cpu"
DEFAULT_BATCH_SIZE = 32

# In-process cache to avoid reloading the model on every function call or Streamlit rerun
_MODEL_CACHE: Dict[tuple, object] = {}


def get_embedding_model(
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE
):
    """
    Loads and caches a SentenceTransformer model instance within the running process.

    Parameters:
        model_name (str): The Hugging Face model identifier or local path.
        device (str): Inference device ("cpu" by default).

    Returns:
        SentenceTransformer: The loaded and cached model instance.
    """
    cache_key = (model_name, device)
    if cache_key not in _MODEL_CACHE:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "The 'sentence-transformers' package is required. "
                "Install it using: pip install sentence-transformers"
            ) from exc

        logger.info("Loading embedding model '%s' on device '%s'...", model_name, device)
        _MODEL_CACHE[cache_key] = SentenceTransformer(model_name, device=device)
        logger.info("Embedding model '%s' loaded successfully.", model_name)

    return _MODEL_CACHE[cache_key]


def get_embedding_dimension(
    model_name: str = DEFAULT_MODEL_NAME,
    device: str = DEFAULT_DEVICE
) -> int:
    """
    Returns the vector dimension produced by the embedding model (e.g., 384 for all-MiniLM-L6-v2).

    Parameters:
        model_name (str): Model identifier.
        device (str): Inference device.

    Returns:
        int: Dimensionality of output vectors.
    """
    model = get_embedding_model(model_name=model_name, device=device)
    dimension = model.get_sentence_embedding_dimension()
    if dimension is None:
        # Fallback to test vector dimension if method returns None
        dummy = model.encode(["test"], convert_to_numpy=True)
        dimension = dummy.shape[1]
    return int(dimension)


def generate_embeddings(
    chunks: Union[List[Dict], List[str]],
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
    normalize: bool = True,
    device: str = DEFAULT_DEVICE,
    model_instance: Optional[object] = None,
) -> np.ndarray:
    """
    Converts a list of text chunks (or plain strings) into a 2D float32 NumPy array
    compatible with FAISS.

    Parameters:
        chunks: List of chunk dictionaries (each containing a 'text' field) or list of strings.
        model_name (str): Hugging Face model name.
        batch_size (int): Batch size for encoding passages.
        normalize (bool): If True, L2-normalizes vectors so that inner product equals cosine similarity.
        device (str): Device for model inference ("cpu" by default).
        model_instance: Optional preloaded or mock model with an `.encode()` method.

    Returns:
        np.ndarray: 2D array of shape (num_chunks, embedding_dim) with dtype float32.
                    Returns an empty 2D array of shape (0, dim) if chunks is empty.
    """
    if chunks is None or len(chunks) == 0:
        dim = 384
        try:
            if model_instance is not None and hasattr(model_instance, "get_sentence_embedding_dimension"):
                dim = model_instance.get_sentence_embedding_dimension()
            elif model_instance is None:
                dim = get_embedding_dimension(model_name=model_name, device=device)
        except Exception:
            dim = 384
        return np.empty((0, dim), dtype=np.float32)

    # Extract text strings from chunks if list of dicts was provided
    texts: List[str] = []
    for item in chunks:
        if isinstance(item, dict):
            text_val = item.get("text", "")
            texts.append(str(text_val) if text_val is not None else "")
        elif isinstance(item, str):
            texts.append(item)
        else:
            texts.append(str(item))

    # Obtain model instance (use injected mock model if provided, else load cached model)
    model = model_instance if model_instance is not None else get_embedding_model(model_name=model_name, device=device)

    # Encode with SentenceTransformers
    raw_embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=normalize,
        convert_to_numpy=True,
    )

    embeddings = np.asarray(raw_embeddings, dtype=np.float32)

    # Ensure 2D shape (num_samples, dimension)
    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    # Explicit normalization safety fallback if normalize was requested but model didn't normalize
    if normalize and embeddings.shape[0] > 0:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero for zero-vectors
        norms[norms == 0.0] = 1.0
        embeddings = embeddings / norms

    return embeddings.astype(np.float32)


def generate_query_embedding(
    query: str,
    model_name: str = DEFAULT_MODEL_NAME,
    normalize: bool = True,
    device: str = DEFAULT_DEVICE,
    model_instance: Optional[object] = None,
) -> np.ndarray:
    """
    Generates a normalized 2D vector for a single query string ready for FAISS search.

    Parameters:
        query (str): The search query text.
        model_name (str): Hugging Face model identifier.
        normalize (bool): If True, L2-normalizes the vector.
        device (str): Device for inference.
        model_instance: Optional preloaded or mock model.

    Returns:
        np.ndarray: 2D array of shape (1, embedding_dim) with dtype float32.

    Raises:
        ValueError: If query is empty or whitespace-only.
        TypeError: If query is not a string.
    """
    if query is None or not isinstance(query, str):
        raise TypeError(f"Query must be a string, got: {type(query).__name__}")

    stripped_query = query.strip()
    if not stripped_query:
        raise ValueError("Query cannot be empty or whitespace-only.")

    embeddings = generate_embeddings(
        chunks=[stripped_query],
        model_name=model_name,
        batch_size=1,
        normalize=normalize,
        device=device,
        model_instance=model_instance,
    )

    return embeddings
