"""
tests/test_report_generator.py
Comprehensive test suite for Module 6: Final Results UI and Report Export.

Validates:
1. Complete analysis report generation in Markdown, Plain Text, and JSON formats.
2. Handling of partial analysis results (summary only, clauses only, risks only).
3. Handling of completely unexecuted analysis (None or empty).
4. Preservation of document filename, generation timestamp, and metadata.
5. Preservation of verbatim evidence quotes and exact page references.
6. Safe handling of empty clause lists or empty risk lists.
7. Scrubbing and zero-exposure of API keys or environment secrets.
8. State invalidation and session reset behavior when changing documents.
"""

import json
import unittest
from unittest.mock import patch

from utils.report_generator import (
    generate_analysis_report,
    generate_markdown_report,
    generate_text_report,
    generate_json_report,
    format_page_numbers,
)
from app import reset_document_state, initialize_session_state


class TestReportGenerator(unittest.TestCase):
    """Test suite for Module 6 Report Generation."""

    def setUp(self):
        self.sample_filename = "master_agreement_2026.pdf"
        self.sample_timestamp = "2026-10-11 20:00:00 UTC"

        self.sample_extraction = {
            "success": True,
            "filename": self.sample_filename,
            "total_pages": 4,
            "char_count": 8450,
            "word_count": 1320,
            "has_text": True,
        }

        self.sample_complete_analysis = {
            "success": True,
            "summary": {
                "summary_text": "Alpha Corp and Beta LLC entered into an IT Services Agreement.",
                "parties": "Alpha Corp and Beta LLC",
                "purpose": "IT architecture consulting and software implementation",
                "obligations": "Beta LLC to deliver milestones; Alpha Corp to pay fees.",
                "key_dates_and_payments": "Payment net-30 days; late penalty 1.5% per month.",
                "termination_and_disputes": "30 days written notice for convenience; New York governing law.",
                "source_citations": [
                    {"page_number": 1, "source": self.sample_filename},
                    {"page_number": 2, "source": self.sample_filename},
                ],
                "success": True,
            },
            "clauses": [
                {
                    "category": "Payment and compensation",
                    "found": True,
                    "explanation": "Fees are payable within 30 days of invoice receipt.",
                    "evidence": "Invoices shall be paid within thirty (30) days of receipt.",
                    "page_numbers": [2],
                    "source": self.sample_filename,
                },
                {
                    "category": "Termination and notice periods",
                    "found": True,
                    "explanation": "Either party may terminate upon 30 days written notice.",
                    "evidence": "Either party may terminate this agreement with 30 days prior written notice.",
                    "page_numbers": [3],
                    "source": self.sample_filename,
                },
                {
                    "category": "Automatic renewal",
                    "found": False,
                    "explanation": "Not identified in the available text.",
                    "evidence": "Not identified in the available text.",
                    "page_numbers": [],
                    "source": self.sample_filename,
                },
            ],
            "risks": [
                {
                    "risk_category": "Broad liability or indemnification",
                    "severity": "High",
                    "explanation": "Uncapped indemnification for indirect damages.",
                    "evidence": "Provider indemnifies Client without limitation against any third-party claims.",
                    "page_numbers": [3, 4],
                    "clarification_question": "Can indemnification be subject to an aggregate liability cap?",
                    "source": self.sample_filename,
                },
                {
                    "risk_category": "Ambiguous penalties or damages",
                    "severity": "Medium",
                    "explanation": "Daily compounding liquidated damages without grace period.",
                    "evidence": "Late delivery incurs $500 per business day penalty.",
                    "page_numbers": [2],
                    "clarification_question": "Can a 5-business-day cure period be included?",
                    "source": self.sample_filename,
                },
            ],
            "total_clauses_found": 2,
            "total_risks_found": 2,
            "high_severity_risks": 1,
            "risks_evaluated": True,
            "disclaimer": "Informational review only. Not formal legal advice.",
        }

    # 1. Complete Report Generation in Markdown
    def test_complete_report_generation_markdown(self):
        report = generate_analysis_report(
            filename=self.sample_filename,
            extraction_result=self.sample_extraction,
            analysis_result=self.sample_complete_analysis,
            export_format="markdown",
            timestamp=self.sample_timestamp,
        )

        self.assertIn("# LegalLens — Document Analysis Report", report)
        self.assertIn(self.sample_filename, report)
        self.assertIn(self.sample_timestamp, report)
        self.assertIn("4 pages | 1,320 words", report)
        self.assertIn("IMPORTANT LEGAL NOTICE", report)
        self.assertIn("1. Executive Document Summary", report)
        self.assertIn("Alpha Corp and Beta LLC", report)
        self.assertIn("2. Important Clause Inspection", report)
        self.assertIn("Payment and compensation", report)
        self.assertIn("Page 2", report)
        self.assertIn("3. Potential Risk & Liability Audit", report)
        self.assertIn("[HIGH] Broad liability or indemnification", report)
        self.assertIn("Can indemnification be subject to an aggregate liability cap?", report)

    # 2. Complete Report Generation in Plain Text
    def test_complete_report_generation_text(self):
        report = generate_analysis_report(
            filename=self.sample_filename,
            extraction_result=self.sample_extraction,
            analysis_result=self.sample_complete_analysis,
            export_format="text",
            timestamp=self.sample_timestamp,
        )

        self.assertIn("LEGALLENS - LEGAL DOCUMENT ANALYSIS REPORT", report)
        self.assertIn(f"Document Filename : {self.sample_filename}", report)
        self.assertIn("1. EXECUTIVE DOCUMENT SUMMARY", report)
        self.assertIn("2. IMPORTANT CLAUSE INSPECTION", report)
        self.assertIn("3. POTENTIAL RISK & LIABILITY AUDIT", report)
        self.assertIn("[SEVERITY: HIGH]", report)
        self.assertIn("END OF REPORT", report)

    # 3. Complete Report Generation in JSON
    def test_complete_report_generation_json(self):
        report_str = generate_analysis_report(
            filename=self.sample_filename,
            extraction_result=self.sample_extraction,
            analysis_result=self.sample_complete_analysis,
            export_format="json",
            timestamp=self.sample_timestamp,
        )

        data = json.loads(report_str)
        self.assertIn("metadata", data)
        self.assertIn("analysis", data)
        self.assertEqual(data["metadata"]["document_filename"], self.sample_filename)
        self.assertEqual(data["metadata"]["document_metrics"]["total_pages"], 4)
        self.assertEqual(data["analysis"]["total_clauses_found"], 2)
        self.assertEqual(data["analysis"]["high_severity_risks"], 1)
        self.assertEqual(len(data["analysis"]["clauses"]), 3)
        self.assertEqual(len(data["analysis"]["risks"]), 2)

    # 4. Partial Report: Summary Only (Clauses & Risks not run yet)
    def test_partial_report_summary_only(self):
        partial_analysis = {
            "success": True,
            "summary": {
                "summary_text": "Grounded executive summary of contract.",
                "parties": "Party A and Party B",
                "purpose": "Consulting agreement",
                "obligations": "Provide services",
                "key_dates_and_payments": "Payment within 30 days",
                "termination_and_disputes": "30 days notice",
                "source_citations": [{"page_number": 1}],
            },
            "clauses": [],
            "risks": [],
            "total_clauses_found": 0,
            "total_risks_found": 0,
            "high_severity_risks": 0,
            "risks_evaluated": False,
        }

        report = generate_analysis_report(
            filename="partial_doc.pdf",
            extraction_result=self.sample_extraction,
            analysis_result=partial_analysis,
            export_format="markdown",
        )

        self.assertIn("Grounded executive summary of contract.", report)
        self.assertIn("Clause category identification has not been generated yet.", report)
        self.assertIn("Potential risk audit has not been generated yet.", report)

    # 5. Partial Report: Clauses Only (Summary not run yet)
    def test_partial_report_clauses_only(self):
        partial_analysis = {
            "success": True,
            "summary": {},
            "clauses": [
                {
                    "category": "Governing law and dispute resolution",
                    "found": True,
                    "explanation": "Governed by California law.",
                    "evidence": "Laws of California shall apply.",
                    "page_numbers": [4],
                }
            ],
            "risks": [],
            "total_clauses_found": 1,
            "total_risks_found": 0,
            "high_severity_risks": 0,
            "risks_evaluated": False,
        }

        report = generate_analysis_report(
            filename="clauses_only.pdf",
            extraction_result=self.sample_extraction,
            analysis_result=partial_analysis,
            export_format="markdown",
        )

        self.assertIn("Executive summary has not been generated yet.", report)
        self.assertIn("Governing law and dispute resolution", report)
        self.assertIn("California law", report)
        self.assertIn("Potential risk audit has not been generated yet.", report)

    # 6. Completely Unexecuted Analysis (None or empty dict)
    def test_unexecuted_report_handling(self):
        report = generate_analysis_report(
            filename="unexecuted.pdf",
            extraction_result=self.sample_extraction,
            analysis_result=None,
            export_format="markdown",
        )

        self.assertIn("Legal document analysis has not been executed for this document yet.", report)
        self.assertIn("IMPORTANT LEGAL NOTICE", report)

    # 7. Preservation of Exact Page References and Verbatim Evidence Quotes
    def test_preservation_of_page_references_and_evidence(self):
        report = generate_markdown_report(
            filename=self.sample_filename,
            extraction_result=self.sample_extraction,
            analysis_result=self.sample_complete_analysis,
        )

        # Clause evidence quotation
        self.assertIn('"Invoices shall be paid within thirty (30) days of receipt."', report)
        self.assertIn("Page 2", report)

        # Risk evidence quotation
        self.assertIn('"Provider indemnifies Client without limitation against any third-party claims."', report)
        self.assertIn("Pages 3, 4", report)

    # 8. Safe Handling of Empty Clause or Risk Lists
    def test_safe_handling_of_empty_clauses_and_risks(self):
        empty_analysis = {
            "success": True,
            "summary": {
                "summary_text": "Summary of clean NDA.",
            },
            "clauses": [],
            "risks": [],
            "total_clauses_found": 0,
            "total_risks_found": 0,
            "high_severity_risks": 0,
            "risks_evaluated": True,
        }

        report = generate_markdown_report(
            filename="clean_nda.pdf",
            analysis_result=empty_analysis,
        )

        self.assertIn("No specific high-exposure contractual risks flagged during audit.", report)
        self.assertIn("Clause category identification has not been generated yet.", report)

    # 9. No Secret or Credential Exposure
    def test_no_secret_exposure_in_export(self):
        secret_token = "gsk_super_secret_groq_api_key_12345"
        with patch.dict("os.environ", {"LLM_API_KEY": secret_token, "OPENAI_API_KEY": "sk-secret-openai"}):
            report_md = generate_analysis_report(
                filename=self.sample_filename,
                extraction_result=self.sample_extraction,
                analysis_result=self.sample_complete_analysis,
                export_format="markdown",
            )
            report_txt = generate_analysis_report(
                filename=self.sample_filename,
                extraction_result=self.sample_extraction,
                analysis_result=self.sample_complete_analysis,
                export_format="text",
            )
            report_json = generate_analysis_report(
                filename=self.sample_filename,
                extraction_result=self.sample_extraction,
                analysis_result=self.sample_complete_analysis,
                export_format="json",
            )

            for output in (report_md, report_txt, report_json):
                self.assertNotIn(secret_token, output)
                self.assertNotIn("sk-secret-openai", output)
                self.assertNotIn("gsk_", output)

    # 10. Document State Invalidation on New Document / Reset
    def test_document_state_invalidation_on_change(self):
        dummy_session = {}
        with patch("streamlit.session_state", dummy_session):
            initialize_session_state()
            dummy_session["active_file_name"] = "old_contract.pdf"
            dummy_session["extraction_result"] = {"success": True}
            dummy_session["chunks"] = [{"text": "chunk1"}]
            dummy_session["vector_retriever"] = object()
            dummy_session["chat_messages"] = [{"role": "user", "content": "hello"}]
            dummy_session["legal_analysis_result"] = {"summary": "old summary"}
            dummy_session["uploader_key"] = 1

            reset_document_state()

            self.assertIsNone(dummy_session["active_file_name"])
            self.assertIsNone(dummy_session["extraction_result"])
            self.assertEqual(dummy_session["chunks"], [])
            self.assertIsNone(dummy_session["vector_retriever"])
            self.assertEqual(dummy_session["chat_messages"], [])
            self.assertIsNone(dummy_session["legal_analysis_result"])
            self.assertEqual(dummy_session["uploader_key"], 2)


if __name__ == "__main__":
    unittest.main()
