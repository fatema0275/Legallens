"""
tests/test_legal_analyzer.py
Test Suite for Module 5: Legal Document Analysis

Covers required scenarios:
1. Document summary generation from mocked LLM response.
2. Clause extraction and output schema validation.
3. Risk identification, severity classification, and clarification questions.
4. Preservation of source and page metadata.
5. Insufficient evidence handling (empty document or passages).
6. Malformed or non-JSON LLM responses handled safely without crashing.
7. Missing or placeholder API key handling.
8. Provider execution failure handling.
9. Documents where some clause categories are missing (found=False, clear indicator).
10. Full end-to-end analyze_legal_document orchestration.
"""

import json
import unittest
from unittest.mock import MagicMock

from modules.legal_analyzer import (
    generate_document_summary,
    identify_important_clauses,
    identify_potential_risks,
    analyze_legal_document,
    safe_parse_json,
    resolve_document_passages,
    LEGAL_DISCLAIMER,
)
from utils.prompts import STANDARD_CLAUSE_CATEGORIES, STANDARD_RISK_CATEGORIES


class MockChoice:
    def __init__(self, content: str):
        self.message = MagicMock()
        self.message.content = content


class MockCompletionResponse:
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]


class MockLLMClient:
    """Mock OpenAI-like chat completion client returning configurable responses."""

    def __init__(self, canned_response: str):
        self.canned_response = canned_response
        self.chat = MagicMock()
        self.chat.completions.create = self._create_completion

    def _create_completion(self, model=None, messages=None, temperature=0.0):
        return MockCompletionResponse(self.canned_response)


class TestLegalAnalyzer(unittest.TestCase):
    """Test suite for Module 5 Legal Document Analysis."""

    def setUp(self):
        self.sample_chunks = [
            {
                "chunk_id": "chunk_1",
                "text": "This Master Services Agreement is entered into by Alpha Corp and Beta LLC. Purpose is IT consulting.",
                "page_number": 1,
                "source": "master_agreement.pdf",
            },
            {
                "chunk_id": "chunk_2",
                "text": "Section 4. Payment terms: Fees shall be paid within 30 days of invoice receipt. Late fees of 1.5% apply.",
                "page_number": 2,
                "source": "master_agreement.pdf",
            },
            {
                "chunk_id": "chunk_3",
                "text": "Section 8. Termination: Either party may terminate with 30 days written notice. Confidentiality survives 3 years.",
                "page_number": 3,
                "source": "master_agreement.pdf",
            },
            {
                "chunk_id": "chunk_4",
                "text": "Section 10. Liability: Neither party's aggregate liability shall exceed $100,000. Governing Law: State of New York.",
                "page_number": 4,
                "source": "master_agreement.pdf",
            },
        ]

    # 1. Summary Generation from Mocked LLM Response
    def test_summary_generation_success(self):
        canned_summary_json = json.dumps(
            {
                "summary_text": "Alpha Corp and Beta LLC entered into a Master Services Agreement for IT consulting services.",
                "parties": "Alpha Corp and Beta LLC",
                "purpose": "IT consulting and software services",
                "obligations": "Beta LLC to provide consulting; Alpha Corp to pay fees.",
                "key_dates_and_payments": "Payment within 30 days; 1.5% late fee.",
                "termination_and_disputes": "30 days notice for termination; New York governing law.",
            }
        )
        mock_client = MockLLMClient(canned_summary_json)

        res = generate_document_summary(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        self.assertIn("Alpha Corp", res["parties"])
        self.assertIn("IT consulting", res["purpose"])
        self.assertIn("30 days", res["key_dates_and_payments"])
        self.assertEqual(len(res["source_citations"]), 4)
        self.assertIsNone(res["error"])

    # 2. Clause Extraction and Expected Output Structure
    def test_clause_extraction_structure(self):
        canned_clauses_json = json.dumps(
            {
                "clauses": [
                    {
                        "category": "Payment and compensation",
                        "found": True,
                        "explanation": "Fees are due within 30 days of invoice with 1.5% late interest.",
                        "evidence": "Fees shall be paid within 30 days of invoice receipt.",
                        "page_numbers": [2],
                    },
                    {
                        "category": "Termination and notice periods",
                        "found": True,
                        "explanation": "Either party may terminate upon 30 days written notice.",
                        "evidence": "Either party may terminate with 30 days written notice.",
                        "page_numbers": [3],
                    },
                    {
                        "category": "Governing law and dispute resolution",
                        "found": True,
                        "explanation": "Agreement is governed by New York state law.",
                        "evidence": "Governing Law: State of New York.",
                        "page_numbers": [4],
                    },
                ]
            }
        )
        mock_client = MockLLMClient(canned_clauses_json)

        res = identify_important_clauses(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        self.assertEqual(len(res["clauses"]), len(STANDARD_CLAUSE_CATEGORIES))
        self.assertGreaterEqual(res["total_found"], 3)

        # Check Payment clause
        payment_clause = next(c for c in res["clauses"] if c["category"] == "Payment and compensation")
        self.assertTrue(payment_clause["found"])
        self.assertIn("30 days", payment_clause["explanation"])
        self.assertEqual(payment_clause["page_numbers"], [2])
        self.assertEqual(payment_clause["source"], "master_agreement.pdf")

    # 3. Handling When Some Clause Categories Are Not Identified
    def test_missing_clause_categories_handled(self):
        canned_partial_json = json.dumps(
            {
                "clauses": [
                    {
                        "category": "Payment and compensation",
                        "found": True,
                        "explanation": "Payment due in 30 days.",
                        "evidence": "Payment within 30 days.",
                        "page_numbers": [2],
                    }
                ]
            }
        )
        mock_client = MockLLMClient(canned_partial_json)

        res = identify_important_clauses(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        # Automatic renewal was not in LLM response, should be present as found=False
        renewal_clause = next(c for c in res["clauses"] if c["category"] == "Automatic renewal")
        self.assertFalse(renewal_clause["found"])
        self.assertEqual(renewal_clause["explanation"], "Not identified in the available text.")
        self.assertEqual(renewal_clause["page_numbers"], [])

    # 4. Risk Identification and Severity Validation
    def test_risk_identification_and_severity(self):
        canned_risks_json = json.dumps(
            {
                "risks": [
                    {
                        "risk_category": "Ambiguous penalties or damages",
                        "severity": "High",
                        "explanation": "1.5% monthly interest on unpaid fees compounds significantly without a cap.",
                        "evidence": "Late fees of 1.5% apply.",
                        "page_numbers": [2],
                        "clarification_question": "Can the late fee interest be capped at a statutory maximum?",
                    },
                    {
                        "risk_category": "Unusually broad liability or indemnification",
                        "severity": "Low",
                        "explanation": "Liability cap is set at $100,000 which is reasonable for standard services.",
                        "evidence": "Neither party's aggregate liability shall exceed $100,000.",
                        "page_numbers": [4],
                        "clarification_question": "Does the cap apply to both direct and consequential damages?",
                    },
                ]
            }
        )
        mock_client = MockLLMClient(canned_risks_json)

        res = identify_potential_risks(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["total_risks"], 2)
        self.assertEqual(res["high_severity_count"], 1)
        self.assertEqual(res["low_severity_count"], 1)

        high_risk = res["risks"][0]
        self.assertEqual(high_risk["severity"], "High")
        self.assertIn("compounds", high_risk["explanation"])
        self.assertEqual(high_risk["page_numbers"], [2])
        self.assertIn("capped", high_risk["clarification_question"])

    # 5. Preservation of Source and Page Metadata
    def test_metadata_preservation(self):
        canned_json = json.dumps(
            {
                "clauses": [
                    {
                        "category": "Confidentiality",
                        "found": True,
                        "explanation": "Confidentiality survives termination for three years.",
                        "evidence": "Confidentiality survives 3 years.",
                        "page_numbers": [3],
                    }
                ]
            }
        )
        mock_client = MockLLMClient(canned_json)

        res = identify_important_clauses(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )

        conf_clause = next(c for c in res["clauses"] if c["category"] == "Confidentiality")
        self.assertEqual(conf_clause["source"], "master_agreement.pdf")
        self.assertEqual(conf_clause["page_numbers"], [3])

    # 6. Insufficient Evidence / Empty Document Handling
    def test_empty_document_handling(self):
        summary_res = generate_document_summary(
            document_data=[],
            llm_config={"api_key": "test_key"},
            client_instance=MockLLMClient("{}"),
        )
        self.assertFalse(summary_res["success"])
        self.assertIn("No document text", summary_res["error"])

        clauses_res = identify_important_clauses(
            document_data=[],
            llm_config={"api_key": "test_key"},
            client_instance=MockLLMClient("{}"),
        )
        self.assertFalse(clauses_res["success"])
        self.assertEqual(clauses_res["total_found"], 0)

        risks_res = identify_potential_risks(
            document_data=[],
            llm_config={"api_key": "test_key"},
            client_instance=MockLLMClient("{}"),
        )
        self.assertFalse(risks_res["success"])
        self.assertEqual(risks_res["total_risks"], 0)

    # 7. Malformed and Non-JSON LLM Responses Handled Safely
    def test_malformed_llm_responses(self):
        garbled_text = "Here is my answer: {not valid json... and random text."
        mock_client = MockLLMClient(garbled_text)

        # Summary should safely convert plain string
        summary_res = generate_document_summary(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )
        self.assertTrue(summary_res["success"])
        self.assertIn("Here is my answer", summary_res["summary_text"])

        # Clauses should return normalized default entries without crashing
        clauses_res = identify_important_clauses(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )
        self.assertTrue(clauses_res["success"])
        self.assertEqual(len(clauses_res["clauses"]), len(STANDARD_CLAUSE_CATEGORIES))

        # Risks should safely return empty list without crashing
        risks_res = identify_potential_risks(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )
        self.assertTrue(risks_res["success"])
        self.assertEqual(risks_res["risks"], [])

    # 8. Missing or Placeholder API Key Handled Safely
    def test_missing_api_key_handled_safely(self):
        res = generate_document_summary(
            document_data=self.sample_chunks,
            llm_config={"api_key": ""},
            client_instance=None,
        )
        self.assertFalse(res["success"])
        self.assertIn("LLM API Key Not Configured", res["summary_text"])
        self.assertEqual(res["error"], "Missing or placeholder LLM API key.")

        res_clauses = identify_important_clauses(
            document_data=self.sample_chunks,
            llm_config={"api_key": "your_llm_api_key_here"},
            client_instance=None,
        )
        self.assertFalse(res_clauses["success"])
        self.assertEqual(res_clauses["error"], "Missing or placeholder LLM API key.")

    # 9. Provider Execution Failures Handled Gracefully
    def test_provider_execution_failure(self):
        def failing_call(messages):
            raise RuntimeError("API timeout or rate limit exceeded")

        res = generate_document_summary(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_key"},
            client_instance=failing_call,
        )
        self.assertFalse(res["success"])
        self.assertIn("API timeout", res["error"])

    # 10. Complete Orchestration: analyze_legal_document
    def test_full_analyze_legal_document(self):
        canned_summary = json.dumps(
            {
                "summary_text": "Executive summary of contract.",
                "parties": "Alpha and Beta",
                "purpose": "Consulting",
                "obligations": "Provide services",
                "key_dates_and_payments": "30 days",
                "termination_and_disputes": "30 days notice",
            }
        )
        mock_client = MockLLMClient(canned_summary)

        full_analysis = analyze_legal_document(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_key"},
            client_instance=mock_client,
        )

        self.assertTrue(full_analysis["success"])
        self.assertIn("summary", full_analysis)
        self.assertIn("clauses", full_analysis)
        self.assertIn("risks", full_analysis)
        self.assertEqual(full_analysis["disclaimer"], LEGAL_DISCLAIMER)

    # 11. Resilient Category Matching (numbered, abbreviations, string booleans)
    def test_resilient_category_matching(self):
        canned_resilient_json = json.dumps(
            {
                "clauses": [
                    {
                        "category": "1. Payment & compensation",
                        "found": "true",
                        "explanation": "Payment within 30 days.",
                        "evidence": "Fees due in 30 days.",
                        "page_numbers": [2],
                    },
                    {
                        "category": "Governing Law",
                        "found": True,
                        "explanation": "New York law governs.",
                        "evidence": "State of New York.",
                        "page_numbers": [4],
                    },
                    {
                        "category": "3 - Confidentiality",
                        "found": "false",
                        "explanation": "Not identified in the available text.",
                        "evidence": "Not identified in the available text.",
                        "page_numbers": [],
                    },
                ]
            }
        )
        mock_client = MockLLMClient(canned_resilient_json)

        res = identify_important_clauses(
            document_data=self.sample_chunks,
            llm_config={"api_key": "test_valid_key"},
            client_instance=mock_client,
        )

        self.assertTrue(res["success"])
        # "1. Payment & compensation" should match "Payment and compensation"
        payment = next(c for c in res["clauses"] if c["category"] == "Payment and compensation")
        self.assertTrue(payment["found"])
        self.assertIn("30 days", payment["explanation"])

        # "Governing Law" should match "Governing law and dispute resolution"
        gov_law = next(c for c in res["clauses"] if c["category"] == "Governing law and dispute resolution")
        self.assertTrue(gov_law["found"])
        self.assertIn("New York", gov_law["explanation"])

        # "3 - Confidentiality" with found="false" should have found=False
        conf = next(c for c in res["clauses"] if c["category"] == "Confidentiality")
        self.assertFalse(conf["found"])

        self.assertGreaterEqual(res["total_found"], 2)


if __name__ == "__main__":
    unittest.main()

