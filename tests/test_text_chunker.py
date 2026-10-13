"""
tests/test_text_chunker.py
Comprehensive test suite for Module 2: Text Chunking.
Validates chunking behavior, parameter constraints, metadata preservation, and edge cases.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.text_chunker import chunk_document, validate_chunking_parameters


def test_1_long_document_produces_multiple_chunks():
    """Test 1: A normal document produces multiple chunks when the input is sufficiently long."""
    long_clause = (
        "This Agreement governs the provision of cloud computing services. "
        "The Service Provider covenants to deliver 99.9% uptime availability across all regions. "
        "Failure to achieve the Service Level Agreement shall entitle the Customer to financial credits. "
        "In no event shall either party be liable for punitive, consequential, special, or exemplary damages. "
        "All notices required under this Agreement shall be sent via certified electronic mail. "
    ) * 10  # ~1700 characters

    pages = [{"page_number": 1, "text": long_clause, "source": "cloud_sla.pdf"}]
    chunks = chunk_document(pages, chunk_size=500, chunk_overlap=100)

    assert len(chunks) > 1, f"Expected multiple chunks, got {len(chunks)}"
    assert all("chunk_id" in c for c in chunks)
    print("[PASS] Test 1: Long document produces multiple chunks")


def test_2_adjacent_chunks_overlap():
    """Test 2: Adjacent chunks share overlapping context as expected."""
    text = (
        "Paragraph One introduces the primary commercial terms and payment milestones. "
        "Paragraph Two outlines strict confidentiality obligations and trade secret definitions. "
        "Paragraph Three establishes the governing law, dispute resolution jurisdiction, and legal remedies."
    )
    pages = [{"page_number": 1, "text": text, "source": "contract.pdf"}]
    # Using small chunk size and overlap to force splitting with overlap
    chunks = chunk_document(pages, chunk_size=100, chunk_overlap=30)

    assert len(chunks) >= 2, "Expected at least 2 chunks to verify overlap"

    # Verify overlap exists between chunk 0 and chunk 1:
    # A substring at the end of chunk 0 or beginning of chunk 1 should match
    overlap_found = False
    for i in range(len(chunks) - 1):
        c1_words = set(chunks[i]["text"].split()[-4:])
        c2_words = set(chunks[i + 1]["text"].split()[:4])
        if c1_words.intersection(c2_words):
            overlap_found = True
            break

    assert overlap_found, "Expected adjacent chunks to share overlapping word boundary context"
    print("[PASS] Test 2: Adjacent chunks overlap as expected")


def test_3_short_document_no_unnecessary_splitting():
    """Test 3: Short documents produce a single valid chunk without unnecessary splitting."""
    short_text = "This is a brief non-disclosure clause governing evaluation discussions."
    pages = [{"page_number": 1, "text": short_text, "source": "brief_nda.pdf"}]

    chunks = chunk_document(pages, chunk_size=800, chunk_overlap=150)

    assert len(chunks) == 1, f"Expected 1 chunk for short text, got {len(chunks)}"
    assert chunks[0]["text"] == short_text
    assert chunks[0]["page_number"] == 1
    assert chunks[0]["source"] == "brief_nda.pdf"
    print("[PASS] Test 3: Short document produces single chunk without over-splitting")


def test_4_empty_input_handling():
    """Test 4: Empty input returns an empty list without crashing."""
    assert chunk_document([]) == []
    assert chunk_document(None) == []
    assert chunk_document({"pages": []}) == []
    assert chunk_document([{"page_number": 1, "text": "", "source": "doc.pdf"}]) == []
    print("[PASS] Test 4: Empty input handling")


def test_5_whitespace_only_produces_no_empty_chunks():
    """Test 5: Whitespace-only content does not produce empty or phantom chunks."""
    whitespace_pages = [
        {"page_number": 1, "text": "   \n\n\t  \n   ", "source": "blank.pdf"},
        {"page_number": 2, "text": "\n\n", "source": "blank.pdf"},
    ]
    chunks = chunk_document(whitespace_pages)
    assert len(chunks) == 0, f"Expected 0 chunks for whitespace pages, got {len(chunks)}"
    print("[PASS] Test 5: Whitespace-only content produces no empty chunks")


def test_6_page_numbers_and_source_filenames_preserved():
    """Test 6: Page numbers and source filenames are strictly preserved on every chunk."""
    pages = [
        {"page_number": 1, "text": "Terms of Service Section 1: User Account Registration.", "source": "tos.pdf"},
        {"page_number": 2, "text": "Terms of Service Section 2: Prohibited Conduct and Suspension.", "source": "tos.pdf"},
        {"page_number": 3, "text": "Terms of Service Section 3: Termination and Governing Law.", "source": "tos.pdf"},
    ]
    chunks = chunk_document(pages, chunk_size=300, chunk_overlap=50)

    assert len(chunks) == 3
    for idx, c in enumerate(chunks):
        assert c["page_number"] == idx + 1
        assert c["source"] == "tos.pdf"
        assert c["chunk_id"] == f"chunk_{idx + 1}"
    print("[PASS] Test 6: Page numbers and source filenames preserved")


def test_7_invalid_chunk_size_rejected():
    """Test 7: Invalid chunk size (<= 0 or non-int) raises ValueError."""
    pages = [{"page_number": 1, "text": "Valid text", "source": "doc.pdf"}]

    try:
        chunk_document(pages, chunk_size=0, chunk_overlap=0)
        assert False, "Expected ValueError for chunk_size=0"
    except ValueError as e:
        assert "positive integer" in str(e)

    try:
        chunk_document(pages, chunk_size=-100, chunk_overlap=50)
        assert False, "Expected ValueError for negative chunk_size"
    except ValueError as e:
        assert "positive integer" in str(e)

    print("[PASS] Test 7: Invalid chunk size is rejected")


def test_8_invalid_overlap_rejected():
    """Test 8: Invalid overlap (negative or >= chunk_size) raises ValueError."""
    pages = [{"page_number": 1, "text": "Valid text", "source": "doc.pdf"}]

    # Negative overlap
    try:
        chunk_document(pages, chunk_size=500, chunk_overlap=-10)
        assert False, "Expected ValueError for negative overlap"
    except ValueError as e:
        assert "non-negative integer" in str(e)

    # Overlap >= chunk_size
    try:
        chunk_document(pages, chunk_size=500, chunk_overlap=500)
        assert False, "Expected ValueError for overlap >= chunk_size"
    except ValueError as e:
        assert "strictly smaller" in str(e)

    print("[PASS] Test 8: Invalid overlap is rejected")


def test_9_multiple_pages_processed_correctly():
    """Test 9: Multiple pages from Module 1 extraction structure are processed with exact page attribution."""
    extraction_output = {
        "success": True,
        "filename": "lease_agreement.pdf",
        "total_pages": 3,
        "pages": [
            {
                "page_number": 1,
                "text": "LEASE AGREEMENT\nTenant: John Doe\nPremises: 123 Main St.\nMonthly Rent: $2,000.",
                "source": "lease_agreement.pdf",
            },
            {
                "page_number": 2,
                "text": "SECURITY DEPOSIT\nDeposit amount of $2,000 shall be held in escrow throughout the tenancy.",
                "source": "lease_agreement.pdf",
            },
            {
                "page_number": 3,
                "text": "PET POLICY AND NOISE RESTRICTIONS\nNo pets allowed without written consent. Quiet hours are 10 PM to 8 AM.",
                "source": "lease_agreement.pdf",
            },
        ],
    }

    chunks = chunk_document(extraction_output, chunk_size=400, chunk_overlap=80)
    assert len(chunks) == 3
    assert chunks[0]["page_number"] == 1
    assert "LEASE AGREEMENT" in chunks[0]["text"]
    assert chunks[1]["page_number"] == 2
    assert "SECURITY DEPOSIT" in chunks[1]["text"]
    assert chunks[2]["page_number"] == 3
    assert "PET POLICY" in chunks[2]["text"]
    print("[PASS] Test 9: Multiple pages from extraction output processed correctly")


def test_10_output_structure_suitable_for_embeddings():
    """Test 10: Output structure contains required keys ready for Module 3 embedding generation."""
    sample_pages = [
        {"page_number": 1, "text": "Consulting Agreement effective October 2026.", "source": "agreement.pdf"}
    ]
    chunks = chunk_document(sample_pages, chunk_size=800, chunk_overlap=150)

    assert len(chunks) == 1
    chunk = chunks[0]

    # Required keys for FAISS/LangChain embedding ingestion
    required_keys = {"chunk_id", "text", "source", "page_number", "char_count", "word_count"}
    assert required_keys.issubset(chunk.keys()), f"Missing keys: {required_keys - set(chunk.keys())}"
    assert isinstance(chunk["chunk_id"], str)
    assert isinstance(chunk["text"], str) and len(chunk["text"]) > 0
    assert isinstance(chunk["source"], str)
    assert isinstance(chunk["page_number"], int)
    assert isinstance(chunk["char_count"], int)
    assert isinstance(chunk["word_count"], int)
    print("[PASS] Test 10: Output structure is suitable for downstream embedding generation")


if __name__ == "__main__":
    print("Running Text Chunker Test Suite (10 Test Cases)...")
    test_1_long_document_produces_multiple_chunks()
    test_2_adjacent_chunks_overlap()
    test_3_short_document_no_unnecessary_splitting()
    test_4_empty_input_handling()
    test_5_whitespace_only_produces_no_empty_chunks()
    test_6_page_numbers_and_source_filenames_preserved()
    test_7_invalid_chunk_size_rejected()
    test_8_invalid_overlap_rejected()
    test_9_multiple_pages_processed_correctly()
    test_10_output_structure_suitable_for_embeddings()
    print("\nAll 10 text chunker tests passed successfully!")
