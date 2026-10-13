"""
modules/pdf_processor.py
Module 1: PDF Processing

This module handles:
1. Validating uploaded PDF files (checking byte header and file structure).
2. Extracting readable text page-by-page using PyMuPDF (pymupdf).
3. Preserving page numbers, per-page text, and source filename metadata for RAG chunking.
4. Calculating basic statistics (page count, character count, word count).
5. Gracefully handling edge cases: empty files, encrypted files, scanned/image-only PDFs, corrupted data.
"""

import pymupdf  # PyMuPDF library


def extract_text_from_pdf(pdf_source, filename: str = None) -> dict:
    """
    Extracts readable text and page metadata from a PDF file source.

    Parameters:
        pdf_source: A file-like object (such as Streamlit UploadedFile),
                    bytes, or bytearray.
        filename (str, optional): The name of the source PDF document.
                                  If not provided, attempts to infer from pdf_source.name.

    Returns:
        dict: A structured dictionary containing:
            - success (bool): True if extraction succeeded without fatal errors.
            - filename (str): Source document filename.
            - total_pages (int): Number of pages in the document.
            - full_text (str): Complete combined text extracted across all pages.
            - pages (list): List of page records for downstream RAG chunking:
                [
                    {
                        'page_number': int,   # 1-indexed page number
                        'text': str,          # Clean text of this page
                        'source': str,        # Document filename/source identifier
                        'char_count': int,    # Character count on this page
                        'word_count': int     # Word count on this page
                    },
                    ...
                ]
            - char_count (int): Total character count in full_text.
            - word_count (int): Total word count in full_text.
            - has_text (bool): True if extractable text was found, False if empty/scanned.
            - error (str or None): Error or warning message if any issue arose.
    """
    # Infer filename if not explicitly provided
    resolved_filename = filename or getattr(pdf_source, "name", "document.pdf")

    # Initialize the structured result
    result = {
        "success": False,
        "filename": resolved_filename,
        "total_pages": 0,
        "full_text": "",
        "pages": [],
        "char_count": 0,
        "word_count": 0,
        "has_text": False,
        "error": None,
    }

    # Step 1: Read raw bytes from input
    if pdf_source is None:
        result["error"] = "No document provided. Please upload a PDF file."
        return result

    try:
        if hasattr(pdf_source, "getvalue"):
            # Streamlit UploadedFile has getvalue()
            pdf_bytes = pdf_source.getvalue()
        elif hasattr(pdf_source, "read"):
            pdf_bytes = pdf_source.read()
            # Reset stream position if seekable
            if hasattr(pdf_source, "seek"):
                pdf_source.seek(0)
        elif isinstance(pdf_source, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_source)
        else:
            result["error"] = "Unsupported input type. Expected bytes or file stream."
            return result
    except Exception as e:
        result["error"] = f"Error reading file data: {str(e)}"
        return result

    # Step 2: Validate file is not empty
    if not pdf_bytes or len(pdf_bytes) == 0:
        result["error"] = "The uploaded file is empty (0 bytes). Please upload a valid PDF."
        return result

    # Step 3: Validate PDF magic bytes header (%PDF-)
    stripped_data = pdf_bytes.lstrip()
    if not stripped_data.startswith(b"%PDF-"):
        result["error"] = "Invalid PDF file: Missing standard '%PDF-' header. Please ensure the file is an actual PDF."
        return result

    # Step 4: Open and parse PDF with PyMuPDF
    doc = None
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")

        # Check if the document is password-protected / encrypted
        if doc.is_encrypted:
            result["error"] = "The uploaded PDF is password-protected or encrypted. Please provide an unencrypted PDF."
            return result

        total_pages = len(doc)
        if total_pages == 0:
            result["error"] = "The uploaded PDF contains no pages."
            return result

        result["total_pages"] = total_pages

        pages_data = []
        all_text_sections = []

        # Step 5: Extract text page by page preserving page boundaries
        for page_index in range(total_pages):
            page = doc.load_page(page_index)
            # Extract plain text
            page_text = page.get_text("text") or ""
            cleaned_text = page_text.strip()

            page_words = len(cleaned_text.split())
            page_chars = len(cleaned_text)

            # Store page metadata ready for downstream RAG chunking (Module 2)
            pages_data.append({
                "page_number": page_index + 1,
                "text": cleaned_text,
                "source": resolved_filename,
                "char_count": page_chars,
                "word_count": page_words,
            })

            if cleaned_text:
                all_text_sections.append(f"--- Page {page_index + 1} ---\n{cleaned_text}")

        # Combine text across all pages
        full_text = "\n\n".join(all_text_sections)
        total_word_count = sum(p["word_count"] for p in pages_data)
        total_char_count = sum(p["char_count"] for p in pages_data)

        result["pages"] = pages_data
        result["full_text"] = full_text
        result["word_count"] = total_word_count
        result["char_count"] = total_char_count
        result["has_text"] = total_word_count > 0
        result["success"] = True

        # If zero words were extracted across all pages, warn user about scanned PDF
        if total_word_count == 0:
            result["error"] = (
                "No extractable text was found in this PDF. The document may be a scanned image "
                "or contain non-selectable text. OCR is not supported in this version."
            )

        return result

    except pymupdf.FileDataError as fde:
        result["error"] = f"Corrupted or invalid PDF file: {str(fde)}"
        return result
    except Exception as e:
        result["error"] = f"Failed to extract text from PDF: {str(e)}"
        return result
    finally:
        if doc is not None:
            try:
                doc.close()
            except Exception:
                pass
