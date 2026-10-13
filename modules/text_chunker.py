"""
modules/text_chunker.py
Module 2: Text Chunking

This module takes extracted PDF page records from Module 1 and splits them
into smaller, overlapping text chunks using LangChain's RecursiveCharacterTextSplitter.
Every generated chunk preserves its original page number and source filename.
"""

from typing import Union, List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter


def validate_chunking_parameters(chunk_size: int, chunk_overlap: int) -> None:
    """
    Validates that chunk_size and chunk_overlap meet structural requirements.
    Raises ValueError with a descriptive message if invalid.
    """
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        raise ValueError(f"chunk_size must be a positive integer, got: {chunk_size}")

    if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
        raise ValueError(f"chunk_overlap must be a non-negative integer, got: {chunk_overlap}")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be strictly smaller than chunk_size ({chunk_size})"
        )


def chunk_document(
    pages_or_result: Union[List[Dict], Dict],
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> List[Dict]:
    """
    Splits document pages into overlapping text chunks with preserved metadata.

    Parameters:
        pages_or_result: Either the full extraction result dict from Module 1
                         or a list of page dicts with [{'page_number': int, 'text': str, 'source': str}, ...]
        chunk_size (int): Maximum character length of each chunk (default 800).
        chunk_overlap (int): Number of overlapping characters between adjacent chunks (default 150).

    Returns:
        List[Dict]: A list of chunk dictionaries, each containing:
            - chunk_id (str): Unique sequential identifier (e.g. 'chunk_1')
            - text (str): The chunked text passage
            - source (str): Source PDF filename
            - page_number (int): Original PDF page number (1-indexed)
            - char_count (int): Length of the chunk text
            - word_count (int): Word count of the chunk text
    """
    validate_chunking_parameters(chunk_size, chunk_overlap)

    # Resolve pages list from dictionary or list input
    if isinstance(pages_or_result, dict):
        pages_list = pages_or_result.get("pages", [])
        fallback_source = pages_or_result.get("filename", "document.pdf")
    elif isinstance(pages_or_result, list):
        pages_list = pages_or_result
        fallback_source = "document.pdf"
    elif pages_or_result is None:
        return []
    else:
        raise TypeError(f"Expected list of pages or extraction dict, got {type(pages_or_result).__name__}")

    if not pages_list:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = []
    chunk_counter = 1

    # Process page-by-page to guarantee exact original page number association
    for page_record in pages_list:
        if not isinstance(page_record, dict):
            continue

        raw_text = page_record.get("text", "")
        if not raw_text or not raw_text.strip():
            continue

        page_number = page_record.get("page_number", 1)
        source = page_record.get("source", fallback_source)

        page_segments = splitter.split_text(raw_text)

        for segment in page_segments:
            cleaned_segment = segment.strip()
            # Avoid empty or whitespace-only chunks
            if not cleaned_segment:
                continue

            chunks.append({
                "chunk_id": f"chunk_{chunk_counter}",
                "text": cleaned_segment,
                "source": source,
                "page_number": page_number,
                "char_count": len(cleaned_segment),
                "word_count": len(cleaned_segment.split())
            })
            chunk_counter += 1

    return chunks
