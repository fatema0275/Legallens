"""
Unit & integration tests for pdf_processor.py and pdf_extractor.py
Tests real PDF generation, extraction edge cases, and RAG metadata preservation.
"""

import pymupdf
from pdf_extractor import extract_text_from_pdf as extract_from_root
from modules.pdf_processor import extract_text_from_pdf


def create_sample_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate an in-memory PDF using PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        if text:
            # Insert text at coordinate (50, 72)
            page.insert_text((50, 72), text, fontsize=11)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_valid_pdf_extraction_and_rag_metadata():
    """Test extracting text from a standard 2-page contract PDF and verifying RAG metadata."""
    page1 = "NON-DISCLOSURE AGREEMENT\nThis agreement is made between Company A and Contractor B."
    page2 = "CONFIDENTIALITY OBLIGATIONS\nThe contractor agrees not to disclose proprietary data.\nPayment: $5000."
    pdf_bytes = create_sample_pdf([page1, page2])

    result = extract_text_from_pdf(pdf_bytes, filename="nda_contract.pdf")

    assert result["success"] is True, f"Extraction failed: {result['error']}"
    assert result["total_pages"] == 2, f"Expected 2 pages, got {result['total_pages']}"
    assert result["filename"] == "nda_contract.pdf"
    assert result["has_text"] is True, "Expected has_text to be True"
    assert "NON-DISCLOSURE AGREEMENT" in result["full_text"]
    assert "CONFIDENTIALITY OBLIGATIONS" in result["full_text"]
    assert result["word_count"] > 10, f"Unexpected word count: {result['word_count']}"
    assert result["char_count"] > 50, f"Unexpected char count: {result['char_count']}"
    assert len(result["pages"]) == 2

    # Verify RAG integration metadata on every page
    for idx, page_record in enumerate(result["pages"]):
        assert page_record["page_number"] == idx + 1
        assert page_record["source"] == "nda_contract.pdf"
        assert len(page_record["text"]) > 0
        assert page_record["char_count"] > 0
        assert page_record["word_count"] > 0

    print("[PASS] test_valid_pdf_extraction_and_rag_metadata")


def test_root_backwards_compatibility():
    """Verify that importing from root pdf_extractor works identically."""
    sample_bytes = create_sample_pdf(["Test content for root alias."])
    res = extract_from_root(sample_bytes, filename="test.pdf")
    assert res["success"] is True
    assert res["filename"] == "test.pdf"
    assert res["pages"][0]["source"] == "test.pdf"
    print("[PASS] test_root_backwards_compatibility")


def test_empty_page_pdf():
    """Test PDF that contains pages but no text (e.g., scanned/blank)."""
    pdf_bytes = create_sample_pdf(["", ""])  # 2 blank pages

    result = extract_text_from_pdf(pdf_bytes)

    assert result["success"] is True, "Expected success=True even if no text"
    assert result["total_pages"] == 2
    assert result["has_text"] is False, "Expected has_text to be False"
    assert result["word_count"] == 0
    assert result["error"] is not None
    assert "scanned" in result["error"].lower() or "no extractable text" in result["error"].lower()
    print("[PASS] test_empty_page_pdf")


def test_zero_byte_file():
    """Test handling of 0-byte empty file."""
    result = extract_text_from_pdf(b"")

    assert result["success"] is False
    assert result["has_text"] is False
    assert "empty" in result["error"].lower()
    print("[PASS] test_zero_byte_file")


def test_invalid_header_file():
    """Test handling of non-PDF files (e.g. plain text or arbitrary bytes)."""
    fake_data = b"This is a plain text file, not a PDF document."
    result = extract_text_from_pdf(fake_data)

    assert result["success"] is False
    assert "missing standard '%pdf-'" in result["error"].lower()
    print("[PASS] test_invalid_header_file")


def test_corrupted_pdf_file():
    """Test handling of a corrupted PDF file."""
    corrupted_data = b"%PDF-1.4\nSome corrupted garbage content that cannot be parsed %%EOF"
    result = extract_text_from_pdf(corrupted_data)

    assert result["success"] is False
    assert result["error"] is not None
    print("[PASS] test_corrupted_pdf_file")


def test_stream_uploaded_file_mock():
    """Test handling of file-like object with .getvalue() matching Streamlit UploadedFile."""
    class MockUploadedFile:
        def __init__(self, data: bytes):
            self._data = data
            self.name = "sample_contract.pdf"
        def getvalue(self):
            return self._data

    sample_bytes = create_sample_pdf(["Standard Service Agreement\nPayment term: 30 days."])
    mock_file = MockUploadedFile(sample_bytes)

    result = extract_text_from_pdf(mock_file)
    assert result["success"] is True
    assert result["total_pages"] == 1
    assert result["filename"] == "sample_contract.pdf"
    assert result["pages"][0]["source"] == "sample_contract.pdf"
    assert "Standard Service Agreement" in result["full_text"]
    assert result["word_count"] > 0
    print("[PASS] test_stream_uploaded_file_mock")


if __name__ == "__main__":
    print("Running PDF Processor RAG-Readiness Test Suite...")
    test_valid_pdf_extraction_and_rag_metadata()
    test_root_backwards_compatibility()
    test_empty_page_pdf()
    test_zero_byte_file()
    test_invalid_header_file()
    test_corrupted_pdf_file()
    test_stream_uploaded_file_mock()
    print("\nAll 7 tests passed successfully!")
