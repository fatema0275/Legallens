"""
tests/test_embeddings.py
Test Suite for Module 3: Embedding Generation

Validates:
1. Embedding generation returns correct 2D numpy array and float32 dtype.
2. Normalization produces unit-length vectors (L2 norm = 1.0).
3. Query embedding validation (rejects empty/whitespace, returns correct shape).
4. Empty chunks list handling returns empty 2D array without crashing.
5. Batch encoding processes multiple items properly.
6. Integration test with real SentenceTransformers model (if network/cached).
"""

import unittest
from unittest.mock import MagicMock
import numpy as np

from modules.embeddings import (
    generate_embeddings,
    generate_query_embedding,
    get_embedding_dimension,
)


class MockEmbeddingModel:
    """Deterministic mock embedding model for fast, network-free unit testing."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def get_sentence_embedding_dimension(self) -> int:
        return self.dimension

    def encode(
        self,
        sentences,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ):
        num_items = len(sentences)
        # Create deterministic vectors based on simple string hashing
        vectors = []
        for i, text in enumerate(sentences):
            seed = sum(ord(c) for c in text) if text else i
            np.random.seed(seed % 10000)
            vec = np.random.randn(self.dimension).astype(np.float32)
            if normalize_embeddings:
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)


class TestEmbeddingsModule(unittest.TestCase):

    def setUp(self):
        self.mock_model = MockEmbeddingModel(dimension=384)
        self.sample_chunks = [
            {
                "chunk_id": "chunk_1",
                "text": "This Agreement shall be governed by Delaware state law.",
                "source": "contract.pdf",
                "page_number": 1,
            },
            {
                "chunk_id": "chunk_2",
                "text": "The Service Level Agreement guarantees 99.9% uptime monthly.",
                "source": "contract.pdf",
                "page_number": 2,
            },
        ]

    def test_generate_embeddings_shape_and_dtype(self):
        """Test that generate_embeddings produces a (N, D) float32 numpy array."""
        embeddings = generate_embeddings(
            self.sample_chunks,
            model_instance=self.mock_model,
        )
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.dtype, np.float32)
        self.assertEqual(embeddings.shape, (2, 384))

    def test_embeddings_are_l2_normalized(self):
        """Test that embeddings are normalized to unit length for cosine similarity."""
        embeddings = generate_embeddings(
            self.sample_chunks,
            normalize=True,
            model_instance=self.mock_model,
        )
        for vec in embeddings:
            norm = float(np.linalg.norm(vec))
            self.assertAlmostEqual(norm, 1.0, places=4)

    def test_empty_chunks_returns_empty_2d_array(self):
        """Test that empty or None chunks return an empty 2D array without error."""
        empty_res_1 = generate_embeddings([], model_instance=self.mock_model)
        self.assertEqual(empty_res_1.shape, (0, 384))
        self.assertEqual(empty_res_1.dtype, np.float32)

        empty_res_2 = generate_embeddings(None, model_instance=self.mock_model)
        self.assertEqual(empty_res_2.shape, (0, 384))

    def test_generate_embeddings_with_plain_strings(self):
        """Test that generate_embeddings accepts a list of plain strings."""
        strings = ["First clause", "Second clause"]
        embeddings = generate_embeddings(strings, model_instance=self.mock_model)
        self.assertEqual(embeddings.shape, (2, 384))

    def test_generate_query_embedding_valid(self):
        """Test that generate_query_embedding returns a (1, D) normalized float32 array."""
        q_emb = generate_query_embedding(
            "What is the governing law?",
            model_instance=self.mock_model,
        )
        self.assertEqual(q_emb.shape, (1, 384))
        self.assertEqual(q_emb.dtype, np.float32)
        norm = float(np.linalg.norm(q_emb[0]))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_generate_query_embedding_rejects_empty_whitespace(self):
        """Test that empty or whitespace-only queries raise ValueError."""
        with self.assertRaises(ValueError):
            generate_query_embedding("", model_instance=self.mock_model)

        with self.assertRaises(ValueError):
            generate_query_embedding("   \n\t  ", model_instance=self.mock_model)

    def test_generate_query_embedding_rejects_non_string(self):
        """Test that non-string queries raise TypeError."""
        with self.assertRaises(TypeError):
            generate_query_embedding(None, model_instance=self.mock_model)

        with self.assertRaises(TypeError):
            generate_query_embedding(12345, model_instance=self.mock_model)

    def test_real_model_embedding_generation(self):
        """Integration test: Verify real sentence-transformers model produces 384-d vectors."""
        real_emb = generate_query_embedding("Governing law clause")
        self.assertEqual(real_emb.shape, (1, 384))
        self.assertAlmostEqual(float(np.linalg.norm(real_emb[0])), 1.0, places=4)


if __name__ == "__main__":
    unittest.main()
