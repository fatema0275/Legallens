"""
tests/test_rag_pipeline.py
Test Suite for Module 4: RAG Question Answering

Covers all required scenarios:
1. Relevant chunks being passed to the LLM.
2. Answers being returned in expected format.
3. Insufficient evidence triggering appropriate response.
4. Missing API keys being handled safely.
5. LLM failures being handled gracefully.
6. Source and page metadata being preserved in citations.
7. Question validation (empty/whitespace/types).
8. Real LLM integration test (conditionally executed if real key is configured).
"""

import os
import unittest
from unittest.mock import MagicMock
from modules.rag_pipeline import (
    answer_question,
    get_llm_config,
    is_valid_api_key,
    extract_citations,
)
from modules.retriever import build_faiss_index
from tests.test_embeddings import MockEmbeddingModel
from utils.prompts import INSUFFICIENT_EVIDENCE_PHRASE


class MockChoice:
    def __init__(self, content: str):
        self.message = MagicMock()
        self.message.content = content


class MockCompletionResponse:
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]


class MockLLMClient:
    """Mock OpenAI-like chat completion client for offline deterministic testing."""

    def __init__(self, canned_answer: str = "The payment terms are 30 days upon receipt [Page 1]."):
        self.canned_answer = canned_answer
        self.last_messages = None
        self.last_model = None
        self.chat = MagicMock()
        self.chat.completions.create = self._create_completion

    def _create_completion(self, model, messages, temperature=0.0):
        self.last_model = model
        self.last_messages = messages
        return MockCompletionResponse(self.canned_answer)


class TestRAGPipeline(unittest.TestCase):

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
        ]
        self.retriever = build_faiss_index(self.sample_chunks, model_instance=self.mock_model)

    def test_relevant_chunks_passed_to_llm(self):
        """Scenario 1: Verify retrieved passages and user question are passed into LLM messages."""
        mock_client = MockLLMClient(canned_answer="Payment terms are 30 days [Page 1].")
        res = answer_question(
            question="When must invoices be paid?",
            retriever=self.retriever,
            top_k=2,
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        self.assertIsNotNone(mock_client.last_messages)

        # Confirm user message contains excerpt text
        user_message_content = mock_client.last_messages[1]["content"]
        self.assertIn("thirty (30) days", user_message_content)
        self.assertIn("When must invoices be paid?", user_message_content)
        self.assertIn("Page 1", user_message_content)

    def test_answer_returned_in_expected_format(self):
        """Scenario 2: Verify answer structure contains all required fields."""
        mock_client = MockLLMClient()
        res = answer_question(
            question="What is the payment timeline?",
            retriever=self.retriever,
            top_k=1,
            client_instance=mock_client,
        )

        self.assertIn("answer", res)
        self.assertIn("passages", res)
        self.assertIn("source_citations", res)
        self.assertIn("has_evidence", res)
        self.assertIn("success", res)
        self.assertIn("error", res)
        self.assertIn("model_name", res)

        self.assertTrue(res["success"])
        self.assertIsInstance(res["passages"], list)
        self.assertIsInstance(res["source_citations"], list)
        self.assertTrue(len(res["passages"]) > 0)

    def test_insufficient_evidence_response(self):
        """Scenario 3: Model indicates insufficient evidence; has_evidence is False."""
        insufficient_ans = INSUFFICIENT_EVIDENCE_PHRASE
        mock_client = MockLLMClient(canned_answer=insufficient_ans)

        res = answer_question(
            question="What are the intellectual property dispute rules?",
            retriever=self.retriever,
            top_k=1,
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        self.assertFalse(res["has_evidence"])
        self.assertIn("do not contain sufficient information", res["answer"].lower())

    def test_empty_retriever_triggers_insufficient_evidence(self):
        """Scenario 3b: Empty retriever returns standard insufficient evidence notice."""
        empty_retriever = build_faiss_index([], model_instance=self.mock_model)
        mock_client = MockLLMClient()

        res = answer_question(
            question="What are the governing terms?",
            retriever=empty_retriever,
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        self.assertFalse(res["has_evidence"])
        self.assertEqual(res["answer"], INSUFFICIENT_EVIDENCE_PHRASE)
        self.assertEqual(len(res["passages"]), 0)

    def test_missing_api_key_handled_safely(self):
        """Scenario 4: Missing API key returns guidance without crashing, preserving passages."""
        # Force empty api key
        res = answer_question(
            question="What is the notice period?",
            retriever=self.retriever,
            top_k=1,
            llm_config={"api_key": ""},
            client_instance=None,
        )

        self.assertFalse(res["success"])
        self.assertIn("LLM API Key Not Configured", res["answer"])
        self.assertGreater(len(res["passages"]), 0)
        self.assertEqual(res["passages"][0]["source"], "master_agreement.pdf")

    def test_placeholder_api_key_handled_safely(self):
        """Scenario 4b: Template placeholder API key is detected and handled safely."""
        res = answer_question(
            question="What is the notice period?",
            retriever=self.retriever,
            llm_config={"api_key": "your_llm_api_key_here"},
            client_instance=None,
        )

        self.assertFalse(res["success"])
        self.assertIn("LLM API Key Not Configured", res["answer"])
        self.assertFalse(is_valid_api_key("your_llm_api_key_here"))

    def test_llm_failure_handled_gracefully(self):
        """Scenario 5: LLM API exceptions are caught and returned in error field."""
        failing_client = MagicMock()
        failing_client.chat.completions.create.side_effect = RuntimeError("API Rate Limit Exceeded")

        res = answer_question(
            question="What are termination terms?",
            retriever=self.retriever,
            client_instance=failing_client,
        )

        self.assertFalse(res["success"])
        self.assertIn("Error generating answer", res["answer"])
        self.assertIn("API Rate Limit Exceeded", res["error"])
        # Passages should still be preserved
        self.assertGreater(len(res["passages"]), 0)

    def test_source_and_page_metadata_preserved(self):
        """Scenario 6: Source filename and page number are preserved in citations and passages."""
        mock_client = MockLLMClient()
        res = answer_question(
            question="What is the termination notice period?",
            retriever=self.retriever,
            top_k=2,
            client_instance=mock_client,
        )

        citations = res["source_citations"]
        self.assertGreaterEqual(len(citations), 1)
        self.assertEqual(citations[0]["source"], "master_agreement.pdf")
        self.assertIn(citations[0]["page_number"], [1, 2])

        # Validate passages preserve metadata
        for p in res["passages"]:
            self.assertEqual(p["source"], "master_agreement.pdf")
            self.assertIn("chunk_id", p)
            self.assertIn("page_number", p)
            self.assertIn("score", p)

    def test_question_validation(self):
        """Scenario 7: Empty or invalid questions are rejected with clear errors."""
        mock_client = MockLLMClient()

        with self.assertRaises(ValueError):
            answer_question("", self.retriever, client_instance=mock_client)

        with self.assertRaises(ValueError):
            answer_question("    \t\n ", self.retriever, client_instance=mock_client)

        with self.assertRaises(TypeError):
            answer_question(None, self.retriever, client_instance=mock_client)

        with self.assertRaises(TypeError):
            answer_question(12345, self.retriever, client_instance=mock_client)

    def test_extract_citations_deduplication(self):
        """Test extract_citations utility deduplicates identical page and source pairs."""
        passages = [
            {"page_number": 1, "source": "nda.pdf"},
            {"page_number": 1, "source": "nda.pdf"},
            {"page_number": 2, "source": "nda.pdf"},
        ]
        cites = extract_citations(passages)
        self.assertEqual(len(cites), 2)
        self.assertEqual(cites[0]["page_number"], 1)
        self.assertEqual(cites[1]["page_number"], 2)

    @unittest.skipUnless(
        bool(os.getenv("OPENAI_API_KEY") and is_valid_api_key(os.getenv("OPENAI_API_KEY"))),
        "Skipping real provider integration test because no live OPENAI_API_KEY is configured in .env",
    )
    def test_real_llm_provider_integration(self):
        """Real LLM Integration Test (Executed only if real API key is configured in .env)."""
        res = answer_question(
            question="What are the payment terms?",
            retriever=self.retriever,
            top_k=2,
        )
        self.assertTrue(res["success"])
        self.assertIn("30", res["answer"])


if __name__ == "__main__":
    unittest.main()
