"""
pdf_extractor.py
Backwards-compatibility entry point for Module 1 (PDF Processing).
Re-exports extract_text_from_pdf from modules.pdf_processor.
"""

from modules.pdf_processor import extract_text_from_pdf

__all__ = ["extract_text_from_pdf"]
