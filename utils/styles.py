"""
utils/styles.py
LegalLens — restrained B2B design system.

Design principles:
  • One typeface: Inter (Google Fonts)
  • Type scale: 12 / 14 / 16 / 20 / 28px — weights 400 / 500 / 600 only
  • 8px spacing base — no large decorative gaps
  • Neutral background, near-black text, one muted blue accent (#2563EB)
  • data-testid selectors only — no emotion-cache class names
  • No gradients, no glow/shadow effects, no decorative emoji, no gold borders
"""


def inject_css() -> str:
    """Returns a <style> block for the LegalLens B2B design system."""

    return """
<style>
/* ── Design tokens ─────────────────────────────────────────────────────────── */
:root {
    /* Spacing (8px scale) */
    --sp-1: 4px;
    --sp-2: 8px;
    --sp-3: 12px;
    --sp-4: 16px;
    --sp-5: 20px;
    --sp-6: 24px;
    --sp-8: 32px;
    --sp-10: 40px;

    /* Type scale */
    --text-xs:  12px;
    --text-sm:  14px;
    --text-base: 16px;
    --text-lg:  20px;
    --text-xl:  28px;

    /* Accent */
    --accent:        #2563EB;
    --accent-light:  rgba(37, 99, 235, 0.10);
    --accent-border: rgba(37, 99, 235, 0.25);

    /* Semantic surface (inherits from Streamlit theme vars) */
    --ll-bg:      var(--background-color, #F8F9FA);
    --ll-surface: var(--secondary-background-color, #FFFFFF);
    --ll-text:    var(--text-color, #111827);
    --ll-muted:   #6B7280;
    --ll-border:  #E5E7EB;
    --ll-border-hv: #D1D5DB;

    /* Risk severity — semantic only, never decorative */
    --risk-high-bg:  rgba(220, 38, 38, 0.08);
    --risk-high-fg:  #B91C1C;
    --risk-high-br:  rgba(220, 38, 38, 0.20);
    --risk-med-bg:   rgba(217, 119, 6, 0.08);
    --risk-med-fg:   #B45309;
    --risk-med-br:   rgba(217, 119, 6, 0.20);
    --risk-low-bg:   rgba(37, 99, 235, 0.08);
    --risk-low-fg:   #1D4ED8;
    --risk-low-br:   rgba(37, 99, 235, 0.20);

    --transition: background-color 150ms ease, border-color 150ms ease, color 150ms ease;
}

/* ── Import Inter ──────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* ── Global reset ──────────────────────────────────────────────────────────── */
html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    font-size: var(--text-base) !important;
    line-height: 1.6 !important;
    font-weight: 400 !important;
}
* { box-sizing: border-box; }

/* ── Hide Streamlit chrome ─────────────────────────────────────────────────── */
#MainMenu, footer,
[data-testid="stDeployButton"],
[data-testid="stDecoration"] {
    display: none !important;
}

/* ── Page container ────────────────────────────────────────────────────────── */
[data-testid="stMainBlockContainer"],
.block-container {
    max-width: 960px !important;
    padding: 1.5rem 2rem 3rem !important;
    margin: 0 auto !important;
}

/* ── Typography ────────────────────────────────────────────────────────────── */
h1 {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-xl) !important;
    font-weight: 600 !important;
    line-height: 1.25 !important;
    letter-spacing: -0.02em !important;
    color: var(--ll-text) !important;
    margin: 0 0 var(--sp-4) !important;
}
h2 {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-lg) !important;
    font-weight: 600 !important;
    line-height: 1.3 !important;
    letter-spacing: -0.015em !important;
    color: var(--ll-text) !important;
    margin: 0 0 var(--sp-3) !important;
}
h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-base) !important;
    font-weight: 600 !important;
    line-height: 1.4 !important;
    color: var(--ll-text) !important;
    margin: 0 0 var(--sp-2) !important;
}
[data-testid="stMarkdownContainer"] > p {
    font-size: var(--text-base) !important;
    line-height: 1.6 !important;
    margin-bottom: var(--sp-4) !important;
}
code {
    font-size: var(--text-sm) !important;
    background: var(--ll-surface) !important;
    border: 1px solid var(--ll-border) !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
}

/* ── Wordmark header ───────────────────────────────────────────────────────── */
.ll-wordmark {
    display: flex;
    align-items: baseline;
    gap: var(--sp-2);
    padding: var(--sp-4) 0 var(--sp-6) 0;
    border-bottom: 1px solid var(--ll-border);
    margin-bottom: var(--sp-6);
}
.ll-wordmark-name {
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--ll-text);
    letter-spacing: -0.02em;
}
.ll-wordmark-sep {
    color: var(--ll-border);
    font-size: var(--text-sm);
}
.ll-wordmark-tagline {
    font-size: var(--text-sm);
    color: var(--ll-muted);
    font-weight: 400;
}

/* ── Sidebar ───────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    border-right: 1px solid var(--ll-border) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding: 1.5rem 1.25rem !important;
}
.ll-sidebar-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--ll-muted);
    margin-bottom: var(--sp-2);
    margin-top: var(--sp-4);
}

/* ── Tabs — outer level ────────────────────────────────────────────────────── */
[data-testid="stTabs"] {
    margin-top: var(--sp-4) !important;
}
/* FIX bug-1: restored 8px gap between tabs and proper 8px 16px padding.
   Underline aligns to the tab's full width. */
[data-testid="stTabs"] [data-baseweb="tab-list"],
[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid var(--ll-border) !important;
    gap: var(--sp-2) !important;          /* 8px between tabs */
    padding: 0 !important;
    margin-bottom: var(--sp-6) !important;
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stTabs"] button[data-baseweb="tab"],
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 15px !important;           /* outer tabs: 15px */
    font-weight: 500 !important;
    color: var(--ll-muted) !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: var(--sp-2) var(--sp-4) !important; /* 8px 16px */
    margin-right: 0 !important;           /* gap on parent handles spacing */
    margin-bottom: -1px !important;       /* underline flush with list border */
    cursor: pointer !important;
    transition: var(--transition) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover,
[data-testid="stTabs"] [role="tab"]:hover {
    color: var(--ll-text) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--ll-text) !important;
    font-weight: 600 !important;
    border-bottom-color: var(--ll-text) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: var(--ll-text) !important;
}
/* FIX bug-1 (root cause): reset inner paragraph/span margin without stripping tab padding */
[data-testid="stTabs"] [data-baseweb="tab"] p,
[data-testid="stTabs"] [data-baseweb="tab"] span,
[data-testid="stTabs"] [role="tab"] p,
[data-testid="stTabs"] [role="tab"] span {
    margin: 0 !important;
    padding: 0 !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    color: inherit !important;
    line-height: 1 !important;
    display: inline-flex !important;
    align-items: center !important;
}

/* ── Tabs — inner / nested level (secondary hierarchy) ─────────────────────── */
/* FIX bug-2: inner stTabs made visually secondary (smaller 14px font, lighter weight, tighter 6px 12px padding) */
[data-testid="stTabs"] [data-testid="stTabs"] [data-baseweb="tab-list"],
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] [data-baseweb="tab-list"],
[data-testid="stTabs"] div[role="tabpanel"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: var(--sp-2) !important;           /* 8px between inner tabs */
    margin-bottom: var(--sp-4) !important;
    border-bottom-color: var(--ll-border) !important;
}
[data-testid="stTabs"] [data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] [data-baseweb="tab"],
[data-testid="stTabs"] div[role="tabpanel"] [data-testid="stTabs"] [data-baseweb="tab"] {
    font-size: var(--text-sm) !important;  /* 14px vs outer 15px */
    font-weight: 400 !important;           /* lighter weight */
    padding: 6px var(--sp-3) !important;   /* 6px 12px — tighter padding */
    color: var(--ll-muted) !important;
}
[data-testid="stTabs"] [data-testid="stTabs"] [data-baseweb="tab"]:hover,
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] [data-baseweb="tab"]:hover,
[data-testid="stTabs"] div[role="tabpanel"] [data-testid="stTabs"] [data-baseweb="tab"]:hover {
    color: var(--ll-text) !important;
}
[data-testid="stTabs"] [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] [data-baseweb="tab-panel"] [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] div[role="tabpanel"] [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    font-weight: 500 !important;           /* lighter than outer 600 */
    color: var(--ll-text) !important;
    border-bottom-color: var(--ll-text) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-panel"],
[data-testid="stTabs"] div[role="tabpanel"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* ── Buttons ───────────────────────────────────────────────────────────────── */
/* FIX bug-3: exact 40px height, centered text both axes, 12px gap in horizontal blocks */
.stButton > button,
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button,
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"],
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-secondary"] {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
    height: 40px !important;              /* fixed 40px height */
    min-height: 40px !important;
    max-height: 40px !important;
    padding: 0 var(--sp-4) !important;    /* 16px horizontal padding */
    border-radius: 6px !important;
    cursor: pointer !important;
    transition: var(--transition) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    box-sizing: border-box !important;
}
.stButton > button[kind="primary"],
[data-testid="stButton"] > button[kind="primary"],
button[data-testid="baseButton-primary"],
button[data-testid="stBaseButton-primary"],
button[kind="primary"] {
    background-color: var(--ll-text) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--ll-text) !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover,
[data-testid="stButton"] > button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover,
button[kind="primary"]:hover {
    opacity: 0.88 !important;
}
.stButton > button[kind="primary"] *,
[data-testid="stButton"] > button[kind="primary"] *,
button[data-testid="baseButton-primary"] *,
button[data-testid="stBaseButton-primary"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
.stButton > button[kind="secondary"],
[data-testid="stButton"] > button[kind="secondary"],
button[data-testid="baseButton-secondary"],
button[data-testid="stBaseButton-secondary"],
button[kind="secondary"] {
    background: var(--ll-surface) !important;
    color: var(--ll-text) !important;
    border: 1px solid var(--ll-border) !important;
}
.stButton > button[kind="secondary"]:hover,
[data-testid="stButton"] > button[kind="secondary"]:hover,
button[data-testid="baseButton-secondary"]:hover,
button[data-testid="stBaseButton-secondary"]:hover,
button[kind="secondary"]:hover {
    border-color: var(--ll-border-hv) !important;
    background: var(--ll-bg) !important;
}

/* FIX bug-3 (root cause): eliminate paragraph margin-bottom and line-height inside buttons */
[data-testid="stButton"] > button [data-testid="stMarkdownContainer"],
[data-testid="stDownloadButton"] > button [data-testid="stMarkdownContainer"],
button[data-testid^="baseButton-"] [data-testid="stMarkdownContainer"],
button[data-testid^="stBaseButton-"] [data-testid="stMarkdownContainer"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    height: 100% !important;
}
.stButton > button p,
.stButton > button span,
.stButton > button div,
[data-testid="stButton"] > button p,
[data-testid="stButton"] > button span,
[data-testid="stDownloadButton"] > button p,
[data-testid="stDownloadButton"] > button span,
button[data-testid^="baseButton-"] p,
button[data-testid^="stBaseButton-"] p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: inherit !important;
    font-weight: inherit !important;
    text-align: center !important;
}

/* FIX bug-3: 12px gap between buttons in horizontal rows */
[data-testid="stHorizontalBlock"] {
    gap: var(--sp-3) !important;           /* 12px gap between buttons */
    align-items: center !important;        /* vertically center columns in the row */
}

/* ── Inputs ────────────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background: var(--ll-surface) !important;
    border: 1px solid var(--ll-border) !important;
    border-radius: 6px !important;
    color: var(--ll-text) !important;
    font-size: var(--text-base) !important;
    font-family: 'Inter', sans-serif !important;
    min-height: 40px !important;
    padding: 0 var(--sp-3) !important;
    transition: var(--transition) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    outline: none !important;
    box-shadow: 0 0 0 2px var(--accent-light) !important;
}
[data-testid="stChatInput"] {
    border: 1px solid var(--ll-border) !important;
    border-radius: 8px !important;
    transition: var(--transition) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-light) !important;
}
[data-testid="stChatInput"] textarea {
    font-size: var(--text-base) !important;
    font-family: 'Inter', sans-serif !important;
    color: var(--ll-text) !important;
}

/* ── File uploader ─────────────────────────────────────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background: var(--ll-surface) !important;
    border: 1px dashed var(--ll-border) !important;
    border-radius: 8px !important;
    padding: var(--sp-8) var(--sp-6) !important;
    text-align: center !important;
    transition: var(--transition) !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent) !important;
    background: var(--accent-light) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
    height: 34px !important;
    padding: 0 var(--sp-3) !important;
    border-radius: 6px !important;
    border: 1px solid var(--ll-border) !important;
    background: var(--ll-surface) !important;
    color: var(--ll-text) !important;
    transition: var(--transition) !important;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    border-color: var(--ll-border-hv) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploader"] small {
    display: none !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzone"] span {
    color: var(--ll-muted) !important;
    font-size: var(--text-sm) !important;
}

/* ── Metric cards ──────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--ll-surface) !important;
    border: 1px solid var(--ll-border) !important;
    border-radius: 8px !important;
    padding: var(--sp-4) var(--sp-5) !important;
    transition: var(--transition) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-xs) !important;
    font-weight: 500 !important;
    color: var(--ll-muted) !important;
    margin-bottom: var(--sp-2) !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-xl) !important;
    font-weight: 600 !important;
    color: var(--ll-text) !important;
    font-feature-settings: "tnum" 1 !important;
    line-height: 1.1 !important;
}

/* ── Expanders ─────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--ll-surface) !important;
    border: 1px solid var(--ll-border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    margin-bottom: var(--sp-3) !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Inter', sans-serif !important;
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
    color: var(--ll-text) !important;
    padding: var(--sp-3) var(--sp-4) !important;
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}
[data-testid="stExpander"] summary:hover {
    background: var(--ll-bg) !important;
}
[data-testid="stExpander"] > div:last-child {
    padding: var(--sp-2) var(--sp-4) var(--sp-4) !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    margin: 0 !important;
    font-size: var(--text-sm) !important;
    color: var(--ll-text) !important;
}
[data-testid="stExpander"] summary svg {
    flex-shrink: 0 !important;
}

/* ── Status widget ─────────────────────────────────────────────────────────── */
[data-testid="stStatusWidget"],
[data-testid="stStatus"] {
    border: 1px solid var(--ll-border) !important;
    border-radius: 8px !important;
    background: var(--ll-surface) !important;
    margin: var(--sp-4) 0 !important;
    overflow: hidden !important;
}
[data-testid="stStatusWidget"] summary {
    padding: var(--sp-3) var(--sp-4) !important;
    background: var(--ll-bg) !important;
    list-style: none !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    gap: var(--sp-2) !important;
}
[data-testid="stStatusWidget"] summary p,
[data-testid="stStatusWidget"] summary span {
    font-size: var(--text-sm) !important;
    font-weight: 500 !important;
    margin: 0 !important;
    color: var(--ll-text) !important;
}
[data-testid="stStatusWidget"] > div:not(summary) {
    padding: var(--sp-3) var(--sp-4) !important;
}

/* ── Spinner ───────────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] {
    display: flex !important;
    align-items: center !important;
    gap: var(--sp-2) !important;
    margin: var(--sp-4) 0 !important;
}
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] span {
    font-size: var(--text-sm) !important;
    margin: 0 !important;
    color: var(--ll-text) !important;
}

/* ── Radio ─────────────────────────────────────────────────────────────────── */
[data-testid="stRadio"] div[role="radiogroup"] {
    gap: var(--sp-2) !important;
}
[data-testid="stRadio"] label[data-baseweb="radio"] {
    cursor: pointer !important;
}
[data-testid="stRadio"] [data-testid="stMarkdownContainer"] > p {
    font-size: var(--text-sm) !important;
    margin: 0 !important;
}

/* ── Info / warning banners ────────────────────────────────────────────────── */
[data-testid="stInfo"],
[data-testid="stWarning"],
[data-testid="stError"],
[data-testid="stSuccess"] {
    border-radius: 8px !important;
    font-size: var(--text-sm) !important;
}

/* ── Caption ───────────────────────────────────────────────────────────────── */
.stCaption,
[data-testid="stCaptionContainer"] p {
    font-size: var(--text-xs) !important;
    color: var(--ll-muted) !important;
    line-height: 1.5 !important;
}

/* ── HR ────────────────────────────────────────────────────────────────────── */
hr {
    border-color: var(--ll-border) !important;
    margin: var(--sp-6) 0 !important;
}

/* ── Reset paragraph margins inside controls ───────────────────────────────── */
/* NOTE: tab <p> is intentionally excluded here — the tab section above handles
   it with a scoped selector that avoids stripping padding from the button itself. */
[data-testid="stFileUploader"] p,
[data-testid="stRadio"] label p,
[data-testid="stCheckbox"] label p,
details summary p,
details summary span {
    margin-bottom: 0 !important;
    margin-top: 0 !important;
}

/* ── Hide heading anchor link icons ────────────────────────────────────────── */
/* FIX bug-5: Streamlit injects [data-testid="stHeaderActionElements"] with an
   anchor <a> next to every h1/h2/h3. Hide it entirely. */
[data-testid="stHeaderActionElements"] {
    display: none !important;
}

/* ══════════════════════════════════════════════════════════════════════════════
   LEGALLENS COMPONENT CLASSES
   ══════════════════════════════════════════════════════════════════════════════ */

/* Document info bar (shown when a doc is loaded) */
/* FIX bug-4: added min-height and overflow:visible so long filenames are not
   clipped. align-items:center vertically centers all children in the same row. */
.ll-doc-bar {
    display: flex;
    align-items: center;           /* vertically center name, meta, badge and button */
    justify-content: space-between;
    background: var(--ll-surface);
    border: 1px solid var(--ll-border);
    border-radius: 8px;
    padding: var(--sp-3) var(--sp-4);
    margin-bottom: var(--sp-6);
    min-height: 56px;              /* prevents clipping when filename wraps */
    overflow: visible;             /* was default hidden via parent — make explicit */
    gap: var(--sp-4);
}
.ll-doc-bar-info {
    display: flex;
    flex-direction: column;
    gap: var(--sp-1);
    min-width: 0;                  /* allow text to shrink/wrap inside flex */
    flex: 1 1 auto;
}
.ll-doc-bar-name {
    font-size: var(--text-base);
    font-weight: 600;
    line-height: 1.4;
    padding-top: 1px;
    color: var(--ll-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;       /* truncate very long filenames gracefully */
}
.ll-doc-bar-meta {
    font-size: var(--text-sm);
    color: var(--ll-muted);
    margin-top: 0;                 /* was var(--sp-1) — now handled by gap on parent */
}

/* Content cards */
.ll-card {
    background: var(--ll-surface);
    border: 1px solid var(--ll-border);
    border-radius: 8px;
    padding: var(--sp-5) var(--sp-6);
    margin-bottom: var(--sp-4);
}
.ll-card-sm {
    background: var(--ll-surface);
    border: 1px solid var(--ll-border);
    border-radius: 6px;
    padding: var(--sp-3) var(--sp-4);
    margin-bottom: var(--sp-3);
}

/* Status tags (inline text labels — not pill badges) */
.ll-tag-ready {
    font-size: var(--text-xs);
    font-weight: 600;
    color: #15803D;
    background: rgba(21, 128, 61, 0.08);
    border: 1px solid rgba(21, 128, 61, 0.20);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
}
.ll-tag-pending {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--ll-muted);
    background: var(--ll-bg);
    border: 1px solid var(--ll-border);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
}

/* Citation tags */
.chip-citation {
    display: inline-block;
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--accent);
    background: var(--accent-light);
    border: 1px solid var(--accent-border);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    margin: 0 var(--sp-1) var(--sp-1) 0;
}

/* Clause status tags */
.chip-clause-found {
    font-size: var(--text-xs);
    font-weight: 600;
    color: #15803D;
    background: rgba(21, 128, 61, 0.08);
    border: 1px solid rgba(21, 128, 61, 0.20);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
}
.chip-clause-missing {
    font-size: var(--text-xs);
    font-weight: 500;
    color: var(--ll-muted);
    background: var(--ll-bg);
    border: 1px solid var(--ll-border);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
}

/* Risk severity tags */
.chip-risk-high {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--risk-high-fg);
    background: var(--risk-high-bg);
    border: 1px solid var(--risk-high-br);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.chip-risk-medium {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--risk-med-fg);
    background: var(--risk-med-bg);
    border: 1px solid var(--risk-med-br);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.chip-risk-low {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--risk-low-fg);
    background: var(--risk-low-bg);
    border: 1px solid var(--risk-low-br);
    border-radius: 4px;
    padding: 2px var(--sp-2);
    display: inline-block;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* Relevance bar */
.relevance-bar-track {
    width: 100%;
    height: 4px;
    background: var(--ll-border);
    border-radius: 2px;
    overflow: hidden;
    margin: var(--sp-1) 0 var(--sp-3);
}
.relevance-bar-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
}

/* Disclaimer */
.legal-disclaimer-box {
    background: var(--ll-bg);
    border: 1px solid var(--ll-border);
    border-radius: 6px;
    padding: var(--sp-3) var(--sp-4);
    font-size: var(--text-sm);
    color: var(--ll-muted);
    line-height: 1.5;
    margin-top: var(--sp-6);
}

/* Upload section label */
.ll-upload-label {
    font-size: var(--text-sm);
    font-weight: 600;
    color: var(--ll-text);
    margin-bottom: var(--sp-2);
    display: block;
}
.ll-upload-hint {
    font-size: var(--text-xs);
    color: var(--ll-muted);
    margin-top: var(--sp-2);
}

/* Preset query buttons row */
.ll-preset-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--ll-muted);
    margin-bottom: var(--sp-2);
    display: block;
}

/* Plotly transparent bg */
.js-plotly-plot .plotly { background: transparent !important; }
</style>
"""
