"""
tests/test_retriever.py
Comprehensive Test Suite for Module 3: FAISS Vector Retrieval

Covers all 12 retrieval scenarios specified in the assignment:
1. A valid set of chunks produces an index.
2. Querying the index returns relevant chunks.
3. The original chunk text is preserved.
4. The original page numbers and source filename are preserved.
5. Each result includes a similarity score.
6. A query retrieves no more than the requested top_k results.
7. When top_k exceeds the number of indexed chunks, only available results are returned.
8. Empty chunk input is handled clearly.
9. Empty or whitespace-only queries are rejected with ValueError.
10. Invalid top_k values (<= 0 or non-int) are handled correctly.
11. Query embedding dimension matches the indexed embedding dimension.
12. Retrieval scores are consistent with cosine similarity (identical text scores ~1.0).
"""

import unittest
import numpy as np

from modules.embeddings import get_embedding_dimension
from modules.retriever import (
    VectorRetriever,
    build_faiss_index,
    retrieve_relevant_chunks,
)
from tests.test_embeddings import MockEmbeddingModel


class TestFAISSRetriever(unittest.TestCase):

    def setUp(self):
        self.mock_model = MockEmbeddingModel(dimension=384)
        self.sample_chunks = [
            {
                "chunk_id": "chunk_1",
                "text": "The Customer shall pay invoices within thirty (30) days of receipt.",
                "source": "master_agreement.pdf",
                "page_number": 1,
                "char_count": 68,
                "word_count": 10,
            },
            {
                "chunk_id": "chunk_2",
                "text": "Either party may terminate this Agreement upon sixty (60) days written notice.",
                "source": "master_agreement.pdf",
                "page_number": 2,
                "char_count": 78,
                "word_count": 11,
            },
            {
                "chunk_id": "chunk_3",
                "text": "The Receiving Party agrees to maintain confidential information in strict confidence.",
                "source": "master_agreement.pdf",
                "page_number": 3,
                "char_count": 86,
                "word_count": 10,
            },
        ]

    def test_scenario_1_valid_chunks_produce_index(self):
        """Scenario 1: A valid set of chunks produces an index."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        self.assertIsNotNone(retriever.index)
        self.assertEqual(retriever.index.ntotal, 3)
        self.assertEqual(retriever.total_chunks, 3)
        self.assertEqual(retriever.dimension, 384)

    def test_scenario_2_querying_returns_chunks(self):
        """Scenario 2: Querying the index returns relevant chunks."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results = retriever.retrieve("payment terms invoices", top_k=2, model_instance=self.mock_model)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

    def test_scenario_3_original_text_preserved(self):
        """Scenario 3: The original chunk text is preserved in retrieved results."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results = retriever.retrieve("terminate agreement notice", top_k=3, model_instance=self.mock_model)
        retrieved_texts = [r["text"] for r in results]
        original_texts = [c["text"] for c in self.sample_chunks]
        for t in retrieved_texts:
            self.assertIn(t, original_texts)

    def test_scenario_4_page_number_and_source_preserved(self):
        """Scenario 4: Original page numbers and source filename are strictly preserved."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results = retriever.retrieve("confidential information", top_k=3, model_instance=self.mock_model)
        for r in results:
            self.assertEqual(r["source"], "master_agreement.pdf")
            self.assertIn(r["page_number"], [1, 2, 3])
            self.assertIn(r["chunk_id"], ["chunk_1", "chunk_2", "chunk_3"])

    def test_scenario_5_similarity_score_included(self):
        """Scenario 5: Each result includes a numerical similarity score."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results = retriever.retrieve("invoices payment", top_k=2, model_instance=self.mock_model)
        for r in results:
            self.assertIn("score", r)
            self.assertIsInstance(r["score"], float)
            # Cosine similarity score range
            self.assertTrue(-1.0 <= r["score"] <= 1.05)

    def test_scenario_6_retrieves_no_more_than_top_k(self):
        """Scenario 6: A query retrieves no more than the requested top_k results."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results_1 = retriever.retrieve("payment", top_k=1, model_instance=self.mock_model)
        self.assertEqual(len(results_1), 1)

        results_2 = retriever.retrieve("payment", top_k=2, model_instance=self.mock_model)
        self.assertEqual(len(results_2), 2)

    def test_scenario_7_top_k_exceeds_available_chunks(self):
        """Scenario 7: When top_k exceeds indexed chunks, only available results are returned."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results = retriever.retrieve("contract clause", top_k=10, model_instance=self.mock_model)
        # Only 3 chunks exist
        self.assertEqual(len(results), 3)

    def test_scenario_8_empty_chunk_input_handled(self):
        """Scenario 8: Empty chunk input produces an empty retriever without crashing."""
        retriever = build_faiss_index([], model_instance=self.mock_model)
        self.assertEqual(retriever.total_chunks, 0)
        self.assertEqual(retriever.index.ntotal, 0)

        # Retrieving from an empty index returns empty list
        results = retriever.retrieve("any query", top_k=3, model_instance=self.mock_model)
        self.assertEqual(results, [])

    def test_scenario_9_empty_whitespace_queries_rejected(self):
        """Scenario 9: Empty or whitespace-only queries are rejected with ValueError."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        with self.assertRaises(ValueError):
            retriever.retrieve("", top_k=3, model_instance=self.mock_model)

        with self.assertRaises(ValueError):
            retriever.retrieve("   \t\n  ", top_k=3, model_instance=self.mock_model)

    def test_scenario_10_invalid_top_k_handled(self):
        """Scenario 10: Invalid top_k values (0, negative, non-int) raise ValueError."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        with self.assertRaises(ValueError):
            retriever.retrieve("test query", top_k=0, model_instance=self.mock_model)

        with self.assertRaises(ValueError):
            retriever.retrieve("test query", top_k=-5, model_instance=self.mock_model)

        with self.assertRaises(ValueError):
            retriever.retrieve("test query", top_k="invalid", model_instance=self.mock_model)

    def test_scenario_11_dimension_mismatch_validation(self):
        """Scenario 11: Query vector dimension mismatch raises ValueError."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        # Mock model with mismatched dimension 128 instead of 384
        mismatched_model = MockEmbeddingModel(dimension=128)
        with self.assertRaises(ValueError):
            retriever.retrieve("test query", top_k=2, model_instance=mismatched_model)

    def test_scenario_12_scores_consistent_with_similarity_metric(self):
        """Scenario 12: Exact matching text yields cosine similarity close to 1.0 and ranks highest."""
        exact_text = self.sample_chunks[0]["text"]
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)
        results = retriever.retrieve(exact_text, top_k=3, model_instance=self.mock_model)

        # Top result should be chunk_1
        self.assertEqual(results[0]["chunk_id"], "chunk_1")
        # Cosine similarity for exact match should be ~1.0
        self.assertAlmostEqual(results[0]["score"], 1.0, places=3)
        # Scores must be sorted descending
        scores = [r["score"] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieve_relevant_chunks_functional_interface(self):
        """Test the functional retrieve_relevant_chunks helper function with both forms."""
        retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)

        # Passing VectorRetriever instance
        res1 = retrieve_relevant_chunks(
            query="invoices",
            retriever_or_index=retriever,
            top_k=2,
            model_instance=self.mock_model,
        )
        self.assertIsInstance(res1, list)
        self.assertEqual(len(res1), 2)

        # Passing dict wrapper
        dict_wrapper = {
            "index": retriever.index,
            "chunks": self.sample_chunks,
            "model_name": retriever.model_name,
        }
        res2 = retrieve_relevant_chunks(
            query="invoices",
            retriever_or_index=dict_wrapper,
            top_k=2,
            model_instance=self.mock_model,
        )
        self.assertEqual(len(res2), 2)

    def test_real_model_integration_retrieval(self):
        """Integration test with the real SentenceTransformers model."""
        real_retriever = build_faiss_index(self.sample_chunks)
        results = real_retriever.retrieve("When do invoices need to be paid?", top_k=1)
        self.assertEqual(len(results), 1)
        # Should identify chunk 1 (payment terms) as top passage
        self.assertEqual(results[0]["chunk_id"], "chunk_1")
        self.assertGreater(results[0]["score"], 0.4)


if __name__ == "__main__":
    unittest.main()
