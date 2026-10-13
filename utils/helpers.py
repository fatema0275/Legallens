"""
utils/helpers.py
Shared helper functions for formatting, citations, and report generation.
Will be populated as pipeline modules are integrated.
"""


def format_page_citation(page_number: int, source: str = "") -> str:
    """Formats a standardized page reference citation string."""
    if source:
        return f"Page {page_number} ({source})"
    return f"Page {page_number}"
