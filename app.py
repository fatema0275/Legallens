"""
LegalLens — Legal Document Analyzer
RAG-powered contract analysis: clause extraction, risk review, grounded Q&A.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Backend modules — unchanged
from modules.pdf_processor import extract_text_from_pdf
from modules.text_chunker import chunk_document
from modules.retriever import build_faiss_index
from modules.rag_pipeline import answer_question, get_llm_config, is_valid_api_key
from modules.legal_analyzer import (
    analyze_legal_document,
    generate_document_summary,
    identify_important_clauses,
    identify_potential_risks,
    LEGAL_DISCLAIMER,
)

# UI utilities
import importlib
import utils.styles
importlib.reload(utils.styles)
from utils.styles import inject_css
from utils.charts import (
    create_words_per_page_chart,
    create_chunk_length_chart,
    create_relevance_scores_chart,
    render_pages_cited_html,
)
from utils.report_generator import generate_analysis_report

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LegalLens",
    page_icon=":material/balance:",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Session state ──────────────────────────────────────────────────────────────
def initialize_session_state():
    """Initializes all required session state keys with safe defaults."""
    defaults = {
        "chat_messages": [],
        "active_file_name": None,
        "extraction_result": None,
        "chunks": [],
        "vector_retriever": None,
        "uploader_key": 0,
        "legal_analysis_result": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_document_state():
    """Clears document, index, and chat state for a fresh session."""
    st.session_state["active_file_name"] = None
    st.session_state["extraction_result"] = None
    st.session_state["chunks"] = []
    st.session_state["vector_retriever"] = None
    st.session_state["chat_messages"] = []
    st.session_state["legal_analysis_result"] = None
    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1


# ── Sidebar ────────────────────────────────────────────────────────────────────
def render_sidebar() -> None:
    """Sidebar: active document info + chunking settings + LLM status."""
    with st.sidebar:
        st.markdown("**LegalLens**")
        st.caption("Legal document analyzer")
        st.divider()

        if st.session_state.get("extraction_result") and st.session_state.get("active_file_name"):
            res = st.session_state["extraction_result"]
            fname = st.session_state["active_file_name"]
            total_pages = res.get("total_pages", 0)
            word_count = res.get("word_count", 0)
            has_index = st.session_state.get("vector_retriever") is not None

            st.markdown(
                f"""
                <div class="ll-card-sm">
                    <div class="ll-doc-bar-name" style="font-size: 14px; word-break: break-all;">{fname}</div>
                    <div class="ll-doc-bar-meta">
                        {total_pages} {'page' if total_pages == 1 else 'pages'} &bull; {word_count:,} words
                    </div>
                    <div style="margin-top: 6px;">
                        {'<span class="ll-tag-ready">Indexed</span>' if has_index else '<span class="ll-tag-pending">Indexing…</span>'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Upload new document",
                key="btn_side_new_doc",
                use_container_width=True,
            ):
                reset_document_state()
                st.rerun()

            st.divider()

        with st.expander("Chunking settings", expanded=False):
            st.number_input(
                "Chunk size (characters)",
                min_value=200,
                max_value=3000,
                value=800,
                step=50,
                key="chunk_size_input",
                help="Target character length for indexed passages.",
            )
            _cs = int(st.session_state.get("chunk_size_input", 800))
            st.number_input(
                "Overlap (characters)",
                min_value=0,
                max_value=max(0, _cs - 50),
                value=min(150, max(0, _cs - 50)),
                step=25,
                key="chunk_overlap_input",
                help="Overlap between adjacent passages to preserve context.",
            )

        # LLM status (always visible, no API key exposed)
        cfg = get_llm_config()
        key_valid = is_valid_api_key(cfg.get("api_key", ""))
        st.divider()
        st.caption(
            f"Provider: {cfg.get('provider', 'openai')} · "
            f"Model: {cfg.get('model_name', '—')} · "
            f"{'API key configured' if key_valid else 'No API key — Q&A shows passages only'}"
        )


# ── Answer display helper ──────────────────────────────────────────────────────
def _render_assistant_answer(
    passages: list,
    citations: list,
    total_pages: int,
    msg_key_prefix: str,
    answer_text: str = "",
    mode: str = "answer",
    error_msg: Optional[str] = None,
):
    """
    Renders an assistant answer.
    mode='answer'   → LLM answer + citations + evidence
    mode='passages' → retrieved passages only
    """
    if mode == "passages":
        if error_msg:
            st.warning(f"Could not generate answer: {error_msg}")
        st.markdown("**Relevant sections**")
    else:
        st.markdown(
            f'<div style="font-size: 16px; line-height: 1.65; color: var(--ll-text);">{answer_text}</div>',
            unsafe_allow_html=True,
        )

    if citations and mode == "answer":
        cited_page_nums = [c["page_number"] for c in citations]
        cites_html = "".join(
            [f'<span class="chip-citation">p. {c["page_number"]}</span>' for c in citations]
        )
        st.markdown(
            f'<div style="margin-top: 10px;"><strong>Sources:</strong> {cites_html}</div>',
            unsafe_allow_html=True,
        )
        strip_html = render_pages_cited_html(
            total_pages=total_pages, cited_pages=cited_page_nums
        )
        st.markdown(strip_html, unsafe_allow_html=True)

    if passages:
        label = (
            f"Evidence ({len(passages)} passages)"
            if mode == "answer"
            else f"Retrieved passages ({len(passages)})"
        )
        with st.expander(label, expanded=(mode == "passages")):
            fig_rel = create_relevance_scores_chart(passages, is_dark=False)
            st.plotly_chart(
                fig_rel, use_container_width=True, config={"displayModeBar": False}
            )
            st.caption("Relevance score from vector similarity search.")

            for idx, p in enumerate(passages, 1):
                cid = p.get("chunk_id", "chunk").upper()
                p_num = p.get("page_number", 1)
                score = p.get("score", 0.0)
                score_pct = round(max(0.0, min(100.0, score * 100)), 1)

                st.markdown(
                    f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:16px;">
                        <span style="font-weight:600; font-size:14px;">
                            Passage {idx} &mdash; <code>{cid}</code> &nbsp; p.&nbsp;{p_num}
                        </span>
                        <span style="font-size:13px; color:var(--accent); font-weight:600;">{score_pct}%</span>
                    </div>
                    <div class="relevance-bar-track">
                        <div class="relevance-bar-fill" style="width:{score_pct}%;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.text_area(
                    f"{msg_key_prefix}_p{idx}",
                    value=p.get("text", ""),
                    height=80,
                    label_visibility="collapsed",
                )


# ── Legal analysis tab ─────────────────────────────────────────────────────────
def render_legal_analysis_tab(res: Dict, chunks: List[Dict]) -> None:
    """Module 5: executive summary, clause inspection, risk audit."""
    st.markdown("## Analysis")

    analysis_res = st.session_state.get("legal_analysis_result")
    retriever = st.session_state.get("vector_retriever")

    # Action row
    col_act1, col_act2, col_act3, col_act4, col_exp, col_clear = st.columns(
        [2.5, 1.6, 1.6, 1.6, 1.4, 1.0]
    )
    with col_act1:
        btn_label = "Run full analysis" if not analysis_res else "Re-run full analysis"
        run_full = st.button(
            btn_label,
            type="primary",
            key="btn_run_full_analysis",
            use_container_width=True,
            help="Summary, 9 clause categories, and risk audit.",
        )
    with col_act2:
        run_summary = st.button(
            "Summary only",
            key="btn_run_summary_only",
            use_container_width=True,
        )
    with col_act3:
        run_clauses = st.button(
            "Clauses only",
            key="btn_run_clauses_only",
            use_container_width=True,
        )
    with col_act4:
        run_risks = st.button(
            "Risks only",
            key="btn_run_risks_only",
            use_container_width=True,
        )
    with col_exp:
        if analysis_res:
            quick_md = generate_analysis_report(
                filename=st.session_state.get("active_file_name", "document.pdf"),
                extraction_result=res,
                analysis_result=analysis_res,
                export_format="markdown",
            )
            base_fname = (st.session_state.get("active_file_name") or "document").rsplit(".", 1)[0]
            st.download_button(
                ":material/download: Export",
                data=quick_md,
                file_name=f"{base_fname}_analysis_report.md",
                mime="text/markdown",
                key="btn_quick_export_analysis",
                use_container_width=True,
            )
    with col_clear:
        if analysis_res:
            if st.button("Clear", key="btn_clear_analysis", use_container_width=True):
                st.session_state["legal_analysis_result"] = None
                st.rerun()

    # Trigger logic
    if run_full:
        with st.status("Analyzing document…", expanded=True) as status:
            st.write("Generating executive summary…")
            analysis_res = analyze_legal_document(document_data=res, retriever=retriever)
            if analysis_res:
                analysis_res["risks_evaluated"] = True
            st.session_state["legal_analysis_result"] = analysis_res
            status.update(label="Analysis complete.", state="complete", expanded=False)
        st.rerun()

    if run_summary:
        with st.status("Generating summary…", expanded=True) as status:
            sum_res = generate_document_summary(document_data=res, retriever=retriever)
            current = st.session_state.get("legal_analysis_result") or {
                "summary": {}, "clauses": [], "risks": [],
                "disclaimer": LEGAL_DISCLAIMER, "total_clauses_found": 0,
                "total_risks_found": 0, "high_severity_risks": 0,
                "risks_evaluated": False, "success": True,
            }
            current["summary"] = sum_res
            current["success"] = sum_res.get("success", False) or current.get("success", False)
            st.session_state["legal_analysis_result"] = current
            status.update(label="Done.", state="complete", expanded=False)
        st.rerun()

    if run_clauses:
        with st.status("Identifying clauses…", expanded=True) as status:
            clause_res = identify_important_clauses(document_data=res, retriever=retriever)
            current = st.session_state.get("legal_analysis_result") or {
                "summary": {}, "clauses": [], "risks": [],
                "disclaimer": LEGAL_DISCLAIMER, "total_clauses_found": 0,
                "total_risks_found": 0, "high_severity_risks": 0,
                "risks_evaluated": False, "success": True,
            }
            current["clauses"] = clause_res.get("clauses", [])
            current["total_clauses_found"] = clause_res.get("total_found", 0)
            current["success"] = clause_res.get("success", False) or current.get("success", False)
            st.session_state["legal_analysis_result"] = current
            status.update(label="Done.", state="complete", expanded=False)
        st.rerun()

    if run_risks:
        with st.status("Auditing risks…", expanded=True) as status:
            risk_res = identify_potential_risks(document_data=res, retriever=retriever)
            current = st.session_state.get("legal_analysis_result") or {
                "summary": {}, "clauses": [], "risks": [],
                "disclaimer": LEGAL_DISCLAIMER, "total_clauses_found": 0,
                "total_risks_found": 0, "high_severity_risks": 0,
                "risks_evaluated": False, "success": True,
            }
            current["risks"] = risk_res.get("risks", [])
            current["total_risks_found"] = risk_res.get("total_risks", 0)
            current["high_severity_risks"] = risk_res.get("high_severity_count", 0)
            current["risks_evaluated"] = True
            current["success"] = risk_res.get("success", False) or current.get("success", False)
            st.session_state["legal_analysis_result"] = current
            status.update(label="Done.", state="complete", expanded=False)
        st.rerun()

    if analysis_res and not analysis_res.get("success") and analysis_res.get("error"):
        st.error(analysis_res.get("error", "Unknown error during analysis."))

    summary = analysis_res.get("summary", {}) if analysis_res else {}
    clauses = analysis_res.get("clauses", []) if analysis_res else []
    risks = analysis_res.get("risks", []) if analysis_res else []
    risks_evaluated = bool(analysis_res.get("risks_evaluated", False)) if analysis_res else False

    # Overview metrics
    if analysis_res:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric(
                "Summary",
                "Ready" if summary.get("summary_text") else "Pending",
            )
        with m2:
            clauses_val = (
                f"{analysis_res.get('total_clauses_found', 0)}/9"
                if clauses else "Pending"
            )
            st.metric("Clauses", clauses_val)
        with m3:
            risks_val = (
                str(analysis_res.get("total_risks_found", len(risks)))
                if risks_evaluated else "Pending"
            )
            st.metric("Risks", risks_val)
        with m4:
            high_sev = (
                str(analysis_res.get("high_severity_risks", 0))
                if risks_evaluated else "Pending"
            )
            st.metric("High severity", high_sev)

    # Sub-tabs
    clauses_tab_title = (
        f"Clauses ({analysis_res.get('total_clauses_found', 0)} found)"
        if analysis_res and clauses
        else "Clauses"
    )
    risks_tab_title = (
        f"Risks ({len(risks)} flagged)"
        if (analysis_res and risks_evaluated)
        else "Risks"
    )

    sub_summary, sub_clauses, sub_risks = st.tabs(
        ["Summary", clauses_tab_title, risks_tab_title]
    )

    # ── Summary sub-tab
    with sub_summary:
        if not summary or not summary.get("summary_text"):
            st.markdown("Run **Summary only** or **Run full analysis** to generate an executive summary.")
            if st.button("Generate summary", key="btn_gen_summary_subtab", type="primary"):
                with st.status("Generating summary…", expanded=True) as status:
                    sum_res = generate_document_summary(document_data=res, retriever=retriever)
                    current = st.session_state.get("legal_analysis_result") or {
                        "summary": {}, "clauses": [], "risks": [],
                        "disclaimer": LEGAL_DISCLAIMER, "total_clauses_found": 0,
                        "total_risks_found": 0, "high_severity_risks": 0,
                        "risks_evaluated": False, "success": True,
                    }
                    current["summary"] = sum_res
                    current["success"] = sum_res.get("success", False) or current.get("success", False)
                    st.session_state["legal_analysis_result"] = current
                    status.update(label="Done.", state="complete", expanded=False)
                st.rerun()
        else:
            st.markdown(
                f"""
                <div class="ll-card">
                    <div style="font-size: 16px; line-height: 1.65; margin-bottom: 16px;">
                        {summary.get("summary_text", "")}
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
                                border-top: 1px solid var(--ll-border); padding-top: 16px;">
                        <div>
                            <div style="font-size: 12px; font-weight: 600; color: var(--ll-muted); margin-bottom: 4px;">Parties</div>
                            <div style="font-size: 14px;">{summary.get("parties", "Not identified.")}</div>
                        </div>
                        <div>
                            <div style="font-size: 12px; font-weight: 600; color: var(--ll-muted); margin-bottom: 4px;">Purpose</div>
                            <div style="font-size: 14px;">{summary.get("purpose", "Not identified.")}</div>
                        </div>
                        <div>
                            <div style="font-size: 12px; font-weight: 600; color: var(--ll-muted); margin-bottom: 4px;">Main obligations</div>
                            <div style="font-size: 14px;">{summary.get("obligations", "Not identified.")}</div>
                        </div>
                        <div>
                            <div style="font-size: 12px; font-weight: 600; color: var(--ll-muted); margin-bottom: 4px;">Key dates &amp; payment</div>
                            <div style="font-size: 14px;">{summary.get("key_dates_and_payments", "Not identified.")}</div>
                        </div>
                        <div style="grid-column: span 2;">
                            <div style="font-size: 12px; font-weight: 600; color: var(--ll-muted); margin-bottom: 4px;">Termination &amp; disputes</div>
                            <div style="font-size: 14px;">{summary.get("termination_and_disputes", "Not identified.")}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            citations = summary.get("source_citations", [])
            if citations:
                cites_html = "".join(
                    [f'<span class="chip-citation">p. {c["page_number"]}</span>' for c in citations]
                )
                st.markdown(
                    f'<div style="margin-top: 4px;"><strong>Sources:</strong> {cites_html}</div>',
                    unsafe_allow_html=True,
                )

    # ── Clauses sub-tab
    with sub_clauses:
        if not clauses:
            st.markdown(
                "Inspects 9 clause categories: Payment, Termination, Confidentiality, "
                "Liability, Penalties, Auto-renewal, IP, Obligations, Governing Law."
            )
            if st.button("Identify clauses", key="btn_gen_clauses_subtab", type="primary"):
                with st.status("Identifying clauses…", expanded=True) as status:
                    clause_res = identify_important_clauses(document_data=res, retriever=retriever)
                    current = st.session_state.get("legal_analysis_result") or {
                        "summary": {}, "clauses": [], "risks": [],
                        "disclaimer": LEGAL_DISCLAIMER, "total_clauses_found": 0,
                        "total_risks_found": 0, "high_severity_risks": 0,
                        "risks_evaluated": False, "success": True,
                    }
                    current["clauses"] = clause_res.get("clauses", [])
                    current["total_clauses_found"] = clause_res.get("total_found", 0)
                    current["success"] = clause_res.get("success", False) or current.get("success", False)
                    st.session_state["legal_analysis_result"] = current
                    status.update(label="Done.", state="complete", expanded=False)
                st.rerun()
        else:
            for idx, clause in enumerate(clauses):
                is_found = clause.get("found", False)
                badge_class = "chip-clause-found" if is_found else "chip-clause-missing"
                badge_text = "Identified" if is_found else "Not found"
                pages_str = (
                    ", ".join(f"p. {p}" for p in clause.get("page_numbers", []))
                    if clause.get("page_numbers")
                    else "—"
                )
                border_color = "var(--accent)" if is_found else "var(--ll-border)"
                st.markdown(
                    f"""
                    <div class="ll-card-sm" style="border-left: 3px solid {border_color}; margin-bottom: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                            <span style="font-weight:600; font-size:14px;">{clause.get('category')}</span>
                            <span class="{badge_class}">{badge_text}</span>
                        </div>
                        <div style="font-size:14px; line-height:1.55; margin-bottom:6px;">{clause.get('explanation')}</div>
                        <div style="font-size:12px; color:var(--ll-muted);">Location: {pages_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if (
                    is_found
                    and clause.get("evidence")
                    and clause.get("evidence") != "Not identified in the available text."
                ):
                    with st.expander(f"Verbatim text — {clause.get('category')}", expanded=False):
                        st.markdown(f'> "{clause.get("evidence")}"')

    # ── Risks sub-tab
    with sub_risks:
        if not risks_evaluated:
            st.markdown(
                "Audits for liability caps, one-sided termination, evergreen renewals, "
                "compounding penalties, and ambiguous dispute procedures."
            )
            if st.button("Audit risks", key="btn_gen_risks_subtab", type="primary"):
                with st.status("Auditing risks…", expanded=True) as status:
                    risk_res = identify_potential_risks(document_data=res, retriever=retriever)
                    current = st.session_state.get("legal_analysis_result") or {
                        "summary": {}, "clauses": [], "risks": [],
                        "disclaimer": LEGAL_DISCLAIMER, "total_clauses_found": 0,
                        "total_risks_found": 0, "high_severity_risks": 0,
                        "risks_evaluated": False, "success": True,
                    }
                    current["risks"] = risk_res.get("risks", [])
                    current["total_risks_found"] = risk_res.get("total_risks", 0)
                    current["high_severity_risks"] = risk_res.get("high_severity_count", 0)
                    current["risks_evaluated"] = True
                    current["success"] = risk_res.get("success", False) or current.get("success", False)
                    st.session_state["legal_analysis_result"] = current
                    status.update(label="Done.", state="complete", expanded=False)
                st.rerun()
        elif not risks:
            st.markdown(
                "No significant risks flagged. The audit did not identify disproportionate "
                "liability caps, asymmetric termination terms, or aggressive renewal clauses."
            )
        else:
            st.caption(
                "The following provisions may warrant closer review or negotiation."
            )
            for r_idx, risk in enumerate(risks):
                sev = risk.get("severity", "Medium")
                if sev == "High":
                    chip_class = "chip-risk-high"
                    border_color = "var(--risk-high-fg)"
                elif sev == "Medium":
                    chip_class = "chip-risk-medium"
                    border_color = "var(--risk-med-fg)"
                else:
                    chip_class = "chip-risk-low"
                    border_color = "var(--risk-low-fg)"

                pages_str = (
                    ", ".join(f"p. {p}" for p in risk.get("page_numbers", []))
                    if risk.get("page_numbers")
                    else "—"
                )

                st.markdown(
                    f"""
                    <div class="ll-card" style="border-left: 3px solid {border_color}; margin-bottom: 12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                            <span style="font-weight:600; font-size:14px;">{risk.get('risk_category')}</span>
                            <span class="{chip_class}">{sev}</span>
                        </div>
                        <div style="font-size:14px; line-height:1.55; margin-bottom:10px;">
                            <strong>Why it matters:</strong> {risk.get('explanation')}
                        </div>
                        <div style="background:var(--ll-bg); border:1px solid var(--ll-border);
                                    border-radius:6px; padding:10px 14px; margin-bottom:8px; font-size:13px;">
                            <strong>Suggested question:</strong> {risk.get('clarification_question')}
                        </div>
                        <div style="font-size:12px; color:var(--ll-muted);">Location: {pages_str}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if (
                    risk.get("evidence")
                    and risk.get("evidence") != "Not identified in the available text."
                ):
                    with st.expander(f"Verbatim text — {risk.get('risk_category')}", expanded=False):
                        st.markdown(f'> "{risk.get("evidence")}"')

    # Disclaimer
    disclaimer_text = (analysis_res.get("disclaimer") if analysis_res else None) or LEGAL_DISCLAIMER
    st.markdown(
        f'<div class="legal-disclaimer-box"><strong>Notice:</strong> {disclaimer_text}</div>',
        unsafe_allow_html=True,
    )


# ── Export tab ─────────────────────────────────────────────────────────────────
def render_report_export_tab(res: Dict, chunks: List[Dict]) -> None:
    """Module 6: multi-format report download."""
    st.markdown("## Export report")
    st.markdown(
        "Download the analysis as Markdown, plain text, or JSON. "
        "Run a full analysis first for complete output."
    )

    filename = st.session_state.get("active_file_name") or res.get("filename", "document.pdf")
    analysis_res = st.session_state.get("legal_analysis_result")
    retriever = st.session_state.get("vector_retriever")

    summary_ready = bool(
        analysis_res and analysis_res.get("summary") and analysis_res["summary"].get("summary_text")
    )
    clauses_ready = bool(analysis_res and analysis_res.get("clauses"))
    risks_ready = bool(analysis_res and analysis_res.get("risks_evaluated"))
    is_complete = summary_ready and clauses_ready and risks_ready

    # Readiness status
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        label = "Ready" if summary_ready else "Pending"
        tag = "ll-tag-ready" if summary_ready else "ll-tag-pending"
        st.markdown(
            f'<div class="ll-card-sm">Summary &nbsp;<span class="{tag}">{label}</span></div>',
            unsafe_allow_html=True,
        )
    with col_s2:
        found_cnt = analysis_res.get("total_clauses_found", 0) if analysis_res else 0
        label = f"Ready ({found_cnt}/9)" if clauses_ready else "Pending"
        tag = "ll-tag-ready" if clauses_ready else "ll-tag-pending"
        st.markdown(
            f'<div class="ll-card-sm">Clauses &nbsp;<span class="{tag}">{label}</span></div>',
            unsafe_allow_html=True,
        )
    with col_s3:
        risk_cnt = len(analysis_res.get("risks", [])) if analysis_res else 0
        label = f"Ready ({risk_cnt} flagged)" if risks_ready else "Pending"
        tag = "ll-tag-ready" if risks_ready else "ll-tag-pending"
        st.markdown(
            f'<div class="ll-card-sm">Risk audit &nbsp;<span class="{tag}">{label}</span></div>',
            unsafe_allow_html=True,
        )

    if not is_complete:
        st.info(
            "Some sections are not yet generated. "
            "You can export with the data available, or run the full analysis first."
        )
        if st.button("Run full analysis", key="btn_export_run_full", type="primary"):
            with st.status("Analyzing document…", expanded=True) as status:
                full_res = analyze_legal_document(document_data=res, retriever=retriever)
                if full_res:
                    full_res["risks_evaluated"] = True
                st.session_state["legal_analysis_result"] = full_res
                status.update(label="Done.", state="complete", expanded=False)
            st.rerun()

    # Format selection and download
    col_fmt, col_btn = st.columns([4, 6])
    with col_fmt:
        export_fmt = st.radio(
            "Format",
            options=["Markdown (.md)", "Plain text (.txt)", "JSON (.json)"],
            index=0,
            key="radio_export_format",
        )

    base_name = filename.rsplit(".", 1)[0] if "." in filename else filename
    if "Markdown" in export_fmt:
        fmt_key, mime_type = "markdown", "text/markdown"
        download_filename = f"{base_name}_analysis_report.md"
    elif "Plain" in export_fmt:
        fmt_key, mime_type = "text", "text/plain"
        download_filename = f"{base_name}_analysis_report.txt"
    else:
        fmt_key, mime_type = "json", "application/json"
        download_filename = f"{base_name}_analysis_report.json"

    report_content = generate_analysis_report(
        filename=filename,
        extraction_result=res,
        analysis_result=analysis_res,
        export_format=fmt_key,
    )

    with col_btn:
        st.markdown('<div style="height:28px;"></div>', unsafe_allow_html=True)
        st.download_button(
            label=f":material/download: Download {download_filename}",
            data=report_content,
            file_name=download_filename,
            mime=mime_type,
            key="btn_download_report_main",
            type="primary",
            use_container_width=True,
        )

    # Preview
    with st.expander("Preview report", expanded=True):
        if fmt_key == "markdown":
            st.markdown(report_content)
        elif fmt_key == "text":
            st.text_area("", value=report_content, height=450, label_visibility="collapsed")
        else:
            st.code(report_content, language="json")


# ── Main application ───────────────────────────────────────────────────────────
def main():
    initialize_session_state()

    # Inject supplemental CSS (config.toml handles the base theme)
    st.markdown(inject_css(), unsafe_allow_html=True)

    # Resolve LLM config
    _cfg = get_llm_config()
    api_key_valid: bool = is_valid_api_key(_cfg.get("api_key", ""))

    # Sidebar
    render_sidebar()

    # Chunk settings from sidebar
    chunk_size = int(st.session_state.get("chunk_size_input", 800))
    chunk_overlap = int(st.session_state.get("chunk_overlap_input", 150))

    has_active_doc = (
        st.session_state.get("extraction_result") is not None
        and st.session_state.get("active_file_name") is not None
    )

    # ── STATE 1: No document loaded ──────────────────────────────────────────
    if not has_active_doc:
        # Wordmark header
        st.markdown(
            """
            <div class="ll-wordmark">
                <span class="ll-wordmark-name">LegalLens</span>
                <span class="ll-wordmark-sep">/</span>
                <span class="ll-wordmark-tagline">Contract analysis</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**Upload a contract to begin**")
        st.markdown(
            "Extract key clauses, review potential risks, and ask plain-language questions "
            "about any PDF contract, NDA, or service agreement.",
        )

        # Upload zone — merged label + dropzone
        uploader_key = f"pdf_uploader_{st.session_state.get('uploader_key', 0)}"

        uploaded_file = st.file_uploader(
            "Drop a PDF here, or click to browse",
            type=["pdf"],
            key=uploader_key,
            label_visibility="visible",
        )
        st.caption("Text-based PDFs only. Processed locally — no data is sent externally.")

        if uploaded_file is not None:
            file_size_kb = len(uploaded_file.getvalue()) / 1024

            st.markdown(
                f"""
                <div class="ll-card-sm" style="display:flex; align-items:center; gap:12px;">
                    <span>:material/description:</span>
                    <div>
                        <div style="font-weight:600; font-size:14px;">{uploaded_file.name}</div>
                        <div style="font-size:12px; color:var(--ll-muted);">{file_size_kb:.1f} KB</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_cancel, col_action = st.columns([1, 2])
            with col_cancel:
                if st.button("Remove", key="btn_cancel_staged_file", use_container_width=True):
                    st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
                    st.rerun()
            with col_action:
                process_btn = st.button(
                    "Extract and index",
                    type="primary",
                    key="btn_extract_index",
                    use_container_width=True,
                )

            if process_btn:
                with st.status("Processing contract…", expanded=True) as status:
                    st.write("Extracting text from PDF…")
                    extraction_result = extract_text_from_pdf(
                        uploaded_file, filename=uploaded_file.name
                    )
                    st.session_state["extraction_result"] = extraction_result
                    st.session_state["active_file_name"] = uploaded_file.name

                    if extraction_result["success"] and extraction_result["has_text"]:
                        st.write("Chunking text into passages…")
                        chunks = chunk_document(
                            extraction_result,
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                        )
                        st.session_state["chunks"] = chunks

                        st.write("Building vector index…")
                        retriever = build_faiss_index(chunks)
                        st.session_state["vector_retriever"] = retriever
                        st.session_state["chat_messages"] = []
                        st.session_state["legal_analysis_result"] = None

                        status.update(
                            label="Ready.",
                            state="complete",
                            expanded=False,
                        )
                        st.rerun()
                    else:
                        st.session_state["chunks"] = []
                        st.session_state["vector_retriever"] = None
                        error_msg = extraction_result.get("error", "Unknown error during extraction.")
                        st.write(f"Error: {error_msg}")
                        status.update(
                            label="Extraction failed.",
                            state="error",
                            expanded=True,
                        )

        # Brief capability list below the uploader
        st.divider()
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**Clause extraction**")
            st.caption(
                "Identifies 9 standard clause categories with verbatim quotes and page citations."
            )
        with col_b:
            st.markdown("**Risk audit**")
            st.caption(
                "Flags liability caps, one-sided termination, auto-renewals, and ambiguous penalties."
            )
        with col_c:
            st.markdown("**Grounded Q&A**")
            st.caption(
                "Answers questions strictly from retrieved passages. "
                "States explicitly when information is absent."
            )

    # ── STATE 2: Document loaded ──────────────────────────────────────────────
    else:
        res = st.session_state["extraction_result"]
        fname = st.session_state["active_file_name"]
        chunks = st.session_state.get("chunks", [])
        total_pages = res.get("total_pages", 1)
        word_count = res.get("word_count", 0)

        # Document info bar
        col_banner_info, col_banner_btn = st.columns([5, 1.2])
        with col_banner_info:
            st.markdown(
                f"""
                <div class="ll-doc-bar">
                    <div class="ll-doc-bar-info">
                        <div class="ll-doc-bar-name">{fname}</div>
                        <div class="ll-doc-bar-meta">
                            {total_pages} {'page' if total_pages == 1 else 'pages'} &bull;
                            {word_count:,} words &bull;
                            {len(chunks)} passages indexed
                        </div>
                    </div>
                    <span class="ll-tag-ready">Ready</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_banner_btn:
            if st.button(
                "Replace",
                key="btn_banner_change_doc",
                use_container_width=True,
            ):
                reset_document_state()
                st.rerun()

        # Workspace tabs — no emoji
        tab_ask, tab_analysis, tab_overview, tab_export = st.tabs(
            ["Ask", "Analysis", "Overview", "Export"]
        )

        # ── TAB 1: Ask ────────────────────────────────────────────────────────
        with tab_ask:
            col_head_title, col_head_clear = st.columns([8, 2])
            with col_head_title:
                st.markdown("## Ask")
            with col_head_clear:
                if st.session_state.get("chat_messages"):
                    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                    if st.button("Clear chat", key="btn_clear_chat", use_container_width=True):
                        st.session_state["chat_messages"] = []
                        st.rerun()

            st.markdown(
                "Ask plain-language questions. Answers are grounded strictly in the document text.",
                unsafe_allow_html=False,
            )

            # Preset questions
            st.caption("Quick questions:")
            col_q1, col_q2, col_q3, col_q4 = st.columns(4)
            preset_query = None
            with col_q1:
                if st.button("Liability cap", use_container_width=True, key="q_liability"):
                    preset_query = "What is the liability cap or aggregate limitation of liability?"
            with col_q2:
                if st.button("Termination terms", use_container_width=True, key="q_termination"):
                    preset_query = "What are the termination clauses, notice periods, and remedies?"
            with col_q3:
                if st.button("Indemnification", use_container_width=True, key="q_indemnity"):
                    preset_query = "What are the indemnification obligations and exclusions?"
            with col_q4:
                if st.button("Governing law", use_container_width=True, key="q_govlaw"):
                    preset_query = "What governing law and jurisdiction apply to this contract?"

            chat_history = st.session_state.get("chat_messages", [])

            # Replay history
            for msg_idx, msg in enumerate(chat_history):
                with st.chat_message(msg["role"]):
                    if msg["role"] == "user":
                        st.markdown(msg["content"])
                    else:
                        _render_assistant_answer(
                            passages=msg.get("passages", []),
                            citations=msg.get("citations", []),
                            total_pages=total_pages,
                            msg_key_prefix=f"hist_{msg_idx}",
                            answer_text=msg.get("content", ""),
                            mode=msg.get("mode", "answer"),
                            error_msg=msg.get("error"),
                        )

            # Chat input
            live_prompt = st.chat_input("Ask a question about this contract…")
            active_query = (
                live_prompt.strip() if (live_prompt and live_prompt.strip()) else preset_query
            )

            if active_query:
                st.session_state["chat_messages"].append(
                    {"role": "user", "content": active_query}
                )
                with st.chat_message("user"):
                    st.markdown(active_query)

                with st.chat_message("assistant"):
                    with st.spinner("Searching contract…"):
                        qa_result = answer_question(
                            question=active_query,
                            retriever=st.session_state["vector_retriever"],
                            top_k=3,
                        )

                    answer_text = qa_result.get("answer", "")
                    citations = qa_result.get("source_citations", [])
                    passages = qa_result.get("passages", [])
                    success = qa_result.get("success", False)
                    err_msg = qa_result.get("error")

                    if success and api_key_valid:
                        mode = "answer"
                    else:
                        mode = "passages"
                        if not citations and passages:
                            from modules.rag_pipeline import extract_citations
                            citations = extract_citations(passages)

                    _render_assistant_answer(
                        passages=passages,
                        citations=citations,
                        total_pages=total_pages,
                        msg_key_prefix=f"live_{len(chat_history)}",
                        answer_text=answer_text,
                        mode=mode,
                        error_msg=err_msg if not success else None,
                    )

                    st.session_state["chat_messages"].append(
                        {
                            "role": "assistant",
                            "content": answer_text if mode == "answer" else "",
                            "citations": citations,
                            "passages": passages,
                            "mode": mode,
                            "error": err_msg if not success else None,
                        }
                    )

        # ── TAB 2: Analysis ───────────────────────────────────────────────────
        with tab_analysis:
            render_legal_analysis_tab(res=res, chunks=chunks)

        # ── TAB 3: Overview ───────────────────────────────────────────────────
        with tab_overview:
            st.markdown("## Overview")

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Pages", res["total_pages"])
            with m2:
                st.metric("Words", f"{res['word_count']:,}")
            with m3:
                st.metric("Passages", len(chunks))
            with m4:
                avg_words = round(res["word_count"] / max(1, res["total_pages"]))
                st.metric("Avg words / page", f"{avg_words:,}")

            if res.get("pages") and len(res["pages"]) > 0:
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("**Word distribution per page**")
                    fig_words = create_words_per_page_chart(res["pages"], is_dark=False)
                    st.plotly_chart(
                        fig_words,
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )
                    st.caption("Content density across document pages.")

                with col_c2:
                    st.markdown("**Passage length distribution**")
                    if chunks:
                        fig_chunks = create_chunk_length_chart(chunks, is_dark=False)
                        st.plotly_chart(
                            fig_chunks,
                            use_container_width=True,
                            config={"displayModeBar": False},
                        )
                        st.caption("Character length across indexed passages.")
                    else:
                        st.caption("No passages available.")

            with st.expander("Full extracted text", expanded=False):
                st.text_area(
                    "",
                    value=res.get("full_text", ""),
                    height=280,
                    label_visibility="collapsed",
                )

            if res["total_pages"] > 1:
                with st.expander(f"Page breakdown ({res['total_pages']} pages)", expanded=False):
                    for page_info in res["pages"]:
                        p_num = page_info["page_number"]
                        p_words = page_info["word_count"]
                        p_chars = page_info["char_count"]
                        st.markdown(
                            f"**Page {p_num}** &mdash; "
                            f'<span style="font-size: 13px; color: var(--ll-muted);">'
                            f"{p_words:,} words, {p_chars:,} characters</span>",
                            unsafe_allow_html=True,
                        )
                        if page_info.get("text"):
                            st.text_area(
                                f"Page {p_num}",
                                value=page_info["text"],
                                height=100,
                                key=f"ov_page_{p_num}",
                                label_visibility="collapsed",
                            )
                        else:
                            st.caption("No selectable text on this page.")

            if chunks:
                with st.expander("Technical details", expanded=False):
                    st.markdown(
                        f"""
                        - **Extraction:** PyMuPDF (`fitz`) page-by-page text extraction
                        - **Chunking:** LangChain Recursive Character Text Splitter ({chunk_size} chars, {chunk_overlap} overlap)
                        - **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` (384-d)
                        - **Index:** FAISS `IndexFlatIP` (cosine similarity via L2-normalized vectors)
                        - **Grounding:** LLM responses constrained to retrieved passages only
                        """
                    )
                    if st.button("Rebuild index with current settings", key="btn_reindex_overview"):
                        with st.spinner("Re-chunking and rebuilding index…"):
                            new_chunks = chunk_document(
                                res, chunk_size=chunk_size, chunk_overlap=chunk_overlap
                            )
                            st.session_state["chunks"] = new_chunks
                            st.session_state["vector_retriever"] = build_faiss_index(new_chunks)
                            st.session_state["legal_analysis_result"] = None
                            st.success(
                                f"Re-indexed {len(new_chunks)} passages "
                                f"({chunk_size} chars, {chunk_overlap} overlap)."
                            )
                            st.rerun()

        # ── TAB 4: Export ─────────────────────────────────────────────────────
        with tab_export:
            render_report_export_tab(res=res, chunks=chunks)


if __name__ == "__main__":
    main()
