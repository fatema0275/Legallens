"""
utils/charts.py
Plotly charting utilities adhering to the Legal Editorial design system.
Includes theme-reactive styling helper, quiet layout options, and specialized charts.
"""

from typing import Dict, List, Any
import plotly.graph_objects as go


def get_chart_palette(is_dark: bool = False) -> Dict[str, Any]:
    """Returns the curated Legal Editorial chart palette and theme colors."""
    if is_dark:
        return {
            "text": "#E8EAF0",
            "muted": "#9AA3B5",
            "grid": "#232B3E",
            "bg": "rgba(0,0,0,0)",
            "primary": "#3D527C",
            "accent": "#C9A24B",
            "colors": ["#3D527C", "#C9A24B", "#3E8E8A", "#8E3B46", "#6B7A99"],
            "hover_bg": "#151B2B",
            "hover_border": "#232B3E",
        }
    else:
        return {
            "text": "#1B2233",
            "muted": "#6B7280",
            "grid": "#E6DFD1",
            "bg": "rgba(0,0,0,0)",
            "primary": "#1F2A44",
            "accent": "#A67C2E",
            "colors": ["#1F2A44", "#A67C2E", "#3E8E8A", "#8E3B46", "#6B7A99"],
            "hover_bg": "#FFFFFF",
            "hover_border": "#E6DFD1",
        }


def style_chart(fig: go.Figure, is_dark: bool = False) -> go.Figure:
    """
    Applies the unified Legal Editorial styling to a Plotly figure:
    - Transparent background
    - Clean Inter typography
    - Subtle minimal gridlines & borders
    - Accessible contrast and muted axes
    - Elegant tooltips
    """
    theme = get_chart_palette(is_dark)

    fig.update_layout(
        paper_bgcolor=theme["bg"],
        plot_bgcolor=theme["bg"],
        font=dict(
            family="Inter, -apple-system, sans-serif",
            size=12,
            color=theme["text"],
        ),
        margin=dict(l=35, r=20, t=20, b=35),
        showlegend=False,
        hoverlabel=dict(
            bgcolor=theme["hover_bg"],
            bordercolor=theme["hover_border"],
            font=dict(family="Inter, sans-serif", size=12, color=theme["text"]),
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(color=theme["muted"], size=11),
        title_font=dict(color=theme["text"], size=12),
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=theme["grid"],
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(color=theme["muted"], size=11),
        title_font=dict(color=theme["text"], size=12),
    )

    return fig


def create_words_per_page_chart(pages: List[Dict[str, Any]], is_dark: bool = False) -> go.Figure:
    """Creates a clean bar chart showing word concentration per document page."""
    theme = get_chart_palette(is_dark)
    page_numbers = [f"Page {p.get('page_number', idx + 1)}" for idx, p in enumerate(pages)]
    word_counts = [p.get("word_count", 0) for p in pages]

    fig = go.Figure(
        data=[
            go.Bar(
                x=page_numbers,
                y=word_counts,
                marker=dict(
                    color=theme["primary"],
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{x}</b><br>Word count: %{y:,}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        height=220,
        xaxis_title="",
        yaxis_title="Words",
    )

    return style_chart(fig, is_dark)


def create_chunk_length_chart(chunks: List[Dict[str, Any]], is_dark: bool = False) -> go.Figure:
    """Creates a histogram showing the distribution of chunk character lengths."""
    theme = get_chart_palette(is_dark)
    chunk_lengths = [c.get("char_count", len(c.get("text", ""))) for c in chunks]

    fig = go.Figure(
        data=[
            go.Histogram(
                x=chunk_lengths,
                nbinsx=10,
                marker=dict(
                    color=theme["accent"],
                    line=dict(width=0),
                ),
                hovertemplate="Length range: %{x} chars<br>Chunk count: %{y}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        height=220,
        xaxis_title="Character Length",
        yaxis_title="Chunk Count",
    )

    return style_chart(fig, is_dark)


def create_relevance_scores_chart(passages: List[Dict[str, Any]], is_dark: bool = False) -> go.Figure:
    """
    Creates a horizontal bar chart of relevance percentages for retrieved passages.
    Passages are sorted from highest relevance to lowest.
    """
    theme = get_chart_palette(is_dark)

    labels = []
    scores_pct = []

    # Display in top-down order (Plotly horizontal bars display bottom-to-top by default, so we reverse)
    sorted_passages = sorted(passages, key=lambda x: x.get("score", 0.0), reverse=False)

    for p in sorted_passages:
        page = p.get("page_number", 1)
        cid = p.get("chunk_id", "chunk").upper()
        # Cosine similarity typically ranges 0.0 to 1.0; convert to percentage
        raw_score = float(p.get("score", 0.0))
        pct = max(0.0, min(100.0, raw_score * 100))
        labels.append(f"Page {page} ({cid})")
        scores_pct.append(round(pct, 1))

    fig = go.Figure(
        data=[
            go.Bar(
                x=scores_pct,
                y=labels,
                orientation="h",
                marker=dict(
                    color=theme["accent"],
                    line=dict(width=0),
                ),
                text=[f"{s}%" for s in scores_pct],
                textposition="auto",
                textfont=dict(color=theme["text"], size=11, family="Inter"),
                hovertemplate="<b>%{y}</b><br>Relevance: %{x}%<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        height=max(160, 45 * len(passages)),
        xaxis=dict(range=[0, 105], title="Relevance Score (%)"),
        yaxis=dict(title=""),
        margin=dict(l=110, r=25, t=10, b=30),
    )

    return style_chart(fig, is_dark)


def render_pages_cited_html(total_pages: int, cited_pages: List[int]) -> str:
    """
    Builds the clean 'Pages Cited' strip component.
    Displays page indicator tiles with cited pages highlighted in warm gold.
    """
    cited_set = set(cited_pages)
    blocks_html = []

    # Cap display if document is very large (e.g. up to 40 pages)
    display_limit = min(total_pages, 50)
    for p in range(1, display_limit + 1):
        is_cited = p in cited_set
        cls = "page-block page-block-cited" if is_cited else "page-block page-block-uncited"
        title = f"Page {p} (Cited)" if is_cited else f"Page {p}"
        blocks_html.append(f'<span class="{cls}" title="{title}">{p}</span>')

    if total_pages > display_limit:
        blocks_html.append(f'<span style="font-size: 0.8rem; color: var(--ll-text-muted); margin-left: 6px;">+{total_pages - display_limit} more</span>')

    joined = "".join(blocks_html)
    return f"""
    <div style="margin-top: 0.5rem; margin-bottom: 0.75rem;">
        <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ll-text-muted); font-weight: 600; margin-bottom: 0.35rem;">
            Document Coverage:
        </div>
        <div class="pages-strip-container">
            {joined}
        </div>
    </div>
    """
