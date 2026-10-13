"""
Legal Document Analyzer - Utilities Package
Contains prompt templates, styling system, and charting utilities.
"""

from utils.styles import inject_css
from utils.charts import (
    style_chart,
    create_words_per_page_chart,
    create_chunk_length_chart,
    create_relevance_scores_chart,
    render_pages_cited_html,
)
from utils.report_generator import generate_analysis_report

__all__ = [
    "inject_css",
    "style_chart",
    "create_words_per_page_chart",
    "create_chunk_length_chart",
    "create_relevance_scores_chart",
    "render_pages_cited_html",
    "generate_analysis_report",
]
