# Project Context: Legal Document Analyzer

> **Authoritative Specification:** This document defines the active and authoritative architectural specification for the **Legal Document Analyzer** project. All future work must follow this six-module RAG architecture. Any older five-module, non-RAG plans are obsolete and must not be used. **RAG is mandatory.**

---

## 1. Project Purpose & Scope

* **Project Name:** Legal Document Analyzer
* **Level:** Intermediate Academic Assignment / Prototype
* **Objective:** Develop a Retrieval-Augmented Generation (RAG) powered application that enables users to upload a legal PDF contract, agreement, or NDA, ask questions about its contents, receive grounded answers with exact source passages and page numbers, and review automated legal analysis (summary, key clauses, risk indicators).
* **Disclaimer:** Educational prototype; not a replacement for qualified legal counsel.

---

## 2. Core Architectural Requirement: Mandatory RAG

* The application **must use a RAG pipeline** to ground answers and analysis in retrieved document passages.
* Multi-tenant or vector databases (Pinecone, ChromaDB) are out of scope. Local vector search with **FAISS** is used.
* The application processes **one uploaded document at a time** in an active user session.
* Never send an entire large document to an LLM when retrieval can supply focused, relevant excerpts.

---

## 3. The Six Project Modules & Status

| Module | Title | Primary Technologies | Responsibilities | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Module 1** | **PDF Processing** | Python, Streamlit, PyMuPDF | Upload PDF, validate structure (`%PDF-`), extract text page-by-page, preserve `page_number`, `source` (filename), and text metrics. Display extracted text and statistics. Handle scanned/empty/encrypted PDFs gracefully. | **Completed & Verified** |
| **Module 2** | **Text Chunking** | Python, LangChain Text Splitters | Split extracted legal text into overlapping chunks using `RecursiveCharacterTextSplitter`. Preserves `source` filename, exact `page_number`, and sequential `chunk_id`. Validated boundaries, no empty/whitespace chunks. | **Completed & Verified** |
| **Module 3** | **Embeddings & Retrieval** | Sentence Transformers, FAISS, Python | Convert chunks to embeddings (`all-MiniLM-L6-v2`), index in a local FAISS vector store, retrieve top-k chunks with page references and similarity information. | **Completed & Verified** |
| **Module 4** | **RAG Question Answering** | LangChain / OpenAI API, FAISS Retriever, Python | Accept user queries, retrieve relevant chunks, prompt LLM to produce plain-English grounded answers with supporting citations. Explicit instruction not to invent facts or assume missing terms. | **Completed & Verified** |
| **Module 5** | **Legal Document Analysis** | Python, LLM Prompts, Rule-Based Checks, RAG | Generate concise plain-English summary, detect key clauses (Payment, Termination, Confidentiality, Liability, Renewal), and flag potential risk indicators with review priority levels (Low/Medium/High). Reuse RAG components. | **Completed & Verified** |
| **Module 6** | **Results Interface & Report Export** | Streamlit, Python File Handling | Unified UI: upload status, Q&A interface with citations, analysis dashboard, and downloadable analysis text/markdown/JSON report. | **Completed & Verified** |

---

## 4. Authoritative Technology Stack

* **Programming Language:** Python 3.10+ (current environment: Python 3.12)
* **User Interface:** Streamlit (clean typography, Light/Dark appearance toggle)
* **PDF Extraction:** PyMuPDF (`pymupdf`)
* **Text Chunking:** LangChain text splitters (`langchain-text-splitters`)
* **Embeddings:** Sentence Transformers (`sentence-transformers/all-MiniLM-L6-v2`)
* **Vector Store:** Local FAISS (`faiss-cpu`)
* **RAG Orchestration:** LangChain (`langchain-core`, `langchain-community`)
* **Answer Generation:** Configurable LLM API (keys stored in `.env`, never hardcoded)
* **Legal Analysis:** LLM prompts supplemented by transparent Python rule-based checks
* **Report Export:** Python file handling & Streamlit native download buttons

*Disallowed Technologies:* React, Flask, FastAPI, PostgreSQL, Supabase, Pinecone, ChromaDB, vector DB cloud services, multi-agent frameworks (CrewAI, AutoGen, LangGraph).

---

## 5. Intended Data Flow

```text
PDF Upload
   │
   ▼
[Module 1] PDF Text Extraction
   │  - Page-by-page text
   │  - Metadata: { page_number, source, text, char_count, word_count }
   ▼
[Module 2] Text Chunking (LangChain)
   │  - Overlapping chunks
   │  - Preserves: { source, page_number, chunk_id }
   ▼
[Module 3] Embedding Generation & FAISS Indexing
   │  - Pretrained Sentence Transformer (all-MiniLM-L6-v2)
   │  - Local FAISS vector index
   ▼
[Module 4] RAG Question Answering
   │  - User Query ──► FAISS Search ──► Top-k relevant chunks
   │  - Prompt LLM with retrieved passages & strict grounding rules
   │  - Grounded Answer + Source Page Citations
   ▼
[Module 5] Legal Document Analysis (Summary, Clauses, Risks)
   │  - Reuses retrieved passages & document structure
   ▼
[Module 6] Results Dashboard & Downloadable Report Export
```

---

## 6. Directory Structure

```text
legal-document-analyzer/
│
├── app.py                     # Streamlit application UI
├── requirements.txt           # Active dependencies (expanded module-by-module)
├── README.md                  # Project overview and setup instructions
├── PROJECT_CONTEXT.md         # Authoritative specification & current status
├── .env.example               # Template environment configuration (no secrets)
├── .gitignore                 # Excludes venv/, .env, __pycache__, etc.
├── test_pdf_extractor.py       # Test suite for PDF processing & metadata
│
├── tests/
│   ├── test_text_chunker.py   # Test suite for Module 2 (10 test cases)
│   ├── test_embeddings.py     # Test suite for Module 3 embeddings (8 test cases)
│   ├── test_retriever.py      # Test suite for Module 3 FAISS retriever (14 test cases)
│   └── test_rag_pipeline.py   # Test suite for Module 4 RAG pipeline (11 test cases)
│
├── modules/
│   ├── __init__.py
│   ├── pdf_processor.py       # [Module 1 - ACTIVE] PyMuPDF extraction & page metadata
│   ├── text_chunker.py        # [Module 2 - ACTIVE] LangChain recursive text chunking
│   ├── embeddings.py          # [Module 3 - ACTIVE] Sentence Transformers (all-MiniLM-L6-v2)
│   ├── retriever.py           # [Module 3 - ACTIVE] FAISS vector store & retrieval
│   ├── rag_pipeline.py        # [Module 4 - ACTIVE] RAG Q&A orchestration & LLM API
│   └── legal_analyzer.py      # [Module 5 - ACTIVE] Summary, clauses & risk detection
│
├── utils/
│   ├── __init__.py
│   ├── prompts.py             # System & user prompts for RAG and analysis
│   └── helpers.py             # Citation formatting & export utilities
│
├── sample_documents/
│   ├── .gitkeep
│   └── sample_contract.pdf     # Test agreement for local manual testing
│
└── venv/                      # Local Python virtual environment
```

---

## 7. Module 2 Implementation Details

* **Implementation File:** `modules/text_chunker.py`
* **Technology:** LangChain `RecursiveCharacterTextSplitter` from `langchain-text-splitters`
* **Default Configuration:** `chunk_size = 800` characters, `chunk_overlap = 150` characters. Separators: `["\n\n", "\n", ". ", " ", ""]`.
* **Validation:** Rejects `chunk_size <= 0`, `chunk_overlap < 0`, and `chunk_overlap >= chunk_size` with descriptive `ValueError`.
* **Page-Level Attribution:** Splits page-by-page from Module 1's `pages` list to ensure every chunk strictly reflects its actual source PDF page number rather than guessing post-concatenation.
* **Chunk Data Structure:**
  ```python
  {
      "chunk_id": "chunk_1",     # Sequential identifier
      "text": "...",             # Non-empty trimmed chunk text
      "source": "contract.pdf",  # Origin document filename
      "page_number": 1,          # 1-indexed PDF page
      "char_count": 780,         # Chunk character length
      "word_count": 115          # Chunk word count
  }
  ```
* **Test Suite:** `tests/test_text_chunker.py` covering 10 required test cases (all 10 verified passing).
* **Known Limitations:** If a single legal paragraph exceeds 800 characters without double line breaks, it splits along single line breaks, periods, or spaces to respect the chunk size ceiling while maintaining overlap.

---

## 8. Module 3 Implementation Details

* **Implementation Files:** `modules/embeddings.py`, `modules/retriever.py`
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense embeddings, CPU inference, process-level lazy cache in `_MODEL_CACHE`).
* **Vector Index:** In-memory FAISS `IndexFlatIP` (`faiss-cpu`), mapping inner product to exact cosine similarity on L2-normalized embeddings.
* **Similarity Metric:** Cosine similarity:
  $$\text{score} = \mathbf{q} \cdot \mathbf{d} = \frac{\mathbf{q}}{\|\mathbf{q}\|} \cdot \frac{\mathbf{d}}{\|\mathbf{d}\|} = \cos(\theta) \in [-1.0, 1.0]$$
  Higher scores denote closer semantic alignment.
* **Retrieval Function Interface:**
  - `build_faiss_index(chunks, embeddings=None, model_name=..., device="cpu") -> VectorRetriever`
  - `retrieve_relevant_chunks(query, retriever_or_index, top_k=3) -> List[Dict]`
  - `VectorRetriever.retrieve(query, top_k=3) -> List[Dict]`
* **Retrieved Result Metadata Structure:**
  ```python
  {
      "chunk_id": "chunk_1",     # Sequential identifier from Module 2
      "text": "...",             # Exact original chunk text
      "source": "contract.pdf",  # Origin document filename
      "page_number": 1,          # Exact source PDF page number
      "score": 0.8421,           # Cosine similarity score (rounded to 4 decimal places)
      "char_count": 780,         # Character length
      "word_count": 115          # Word count
  }
  ```
* **How Module 2 Feeds Module 3:**
  The list of chunk records from `modules/text_chunker.py` is passed directly into `build_faiss_index(chunks)`. The retriever preserves the 1-to-1 ordinal mapping between FAISS vector IDs and the original chunk dictionaries, ensuring that all metadata fields (`source`, `page_number`, `chunk_id`) remain intact during top-$k$ retrieval.
* **Hardware & Model Requirements:**
  Runs completely locally on standard CPU without GPU acceleration or cloud API dependencies. Downloads `all-MiniLM-L6-v2` (~90 MB) once on first run, cached locally by Hugging Face Hub in `~/.cache/huggingface/hub`.
* **Testing & Verification:**
  - **Module 1 (`test_pdf_extractor.py`):** 7 tests passed, 0 failed, 0 skipped.
  - **Module 2 (`tests/test_text_chunker.py`):** 10 tests passed, 0 failed, 0 skipped.
  - **Module 3 Embeddings (`tests/test_embeddings.py`):** 8 tests passed, 0 failed, 0 skipped (7 tests executed with deterministic `MockEmbeddingModel`, 1 integration test executed with the real `sentence-transformers/all-MiniLM-L6-v2` model).
  - **Module 3 Retriever (`tests/test_retriever.py`):** 14 tests passed, 0 failed, 0 skipped (13 tests executed with deterministic `MockEmbeddingModel`, 1 integration test executed with the real `sentence-transformers/all-MiniLM-L6-v2` model and FAISS).
  - **Total Test Suite:** 39 passed, 0 failed, 0 skipped.
  - **Streamlit Index Reuse:** Verified that `st.session_state["vector_retriever"]` caches the active document's FAISS index and model instance across app reruns, avoiding redundant embedding generation and model reloads, and clears safely upon new document extraction.
* **Known Limitations:**
  Vector indexes are currently maintained in memory for the active user session. Multi-document persistence or cross-session disk storage is deferred to later architecture phases.

---

## 9. Module 4 Implementation Details

* **Implementation Files:** `modules/rag_pipeline.py`, `utils/prompts.py`
* **Technologies:** Python, `openai` client, `python-dotenv`, FAISS Retriever
* **Provider Support:**
  - Standard OpenAI API (`gpt-3.5-turbo`, `gpt-4o-mini`).
  - Groq fast inference (`llama-3.1-8b-instant` via `https://api.groq.com/openai/v1`).
  - Local Ollama or custom OpenAI-compatible endpoint.
  - Configured strictly via `.env` with no hardcoded credentials.
* **Grounding & Anti-Hallucination:**
  - System prompt enforces zero extrapolation and mandates direct citations (`[Page X]`).
  - Standardized insufficient evidence response:
    *"The provided document excerpts do not contain sufficient information to answer this question."*
  - Automatically flags `has_evidence=False` if the model indicates missing information.
* **Pipeline Interface:**
  - `answer_question(question, retriever, top_k=3, llm_config=None, client_instance=None) -> Dict`
* **Result Data Structure:**
  ```python
  {
      "answer": "...",            # Plain-English grounded answer
      "passages": [...],          # Supporting chunks with scores and page numbers
      "source_citations": [...],  # List of unique [{'page_number': int, 'source': str}]
      "has_evidence": True,       # Boolean indicator of evidence sufficiency
      "success": True,            # Status of retrieval and API execution
      "error": None,              # Descriptive error message if failed
      "model_name": "..."         # Active LLM model name
  }
  ```
* **Testing & Verification:**
  - `tests/test_rag_pipeline.py`: 11 test cases covering passage passing, output schema, insufficient evidence handling, missing API keys, placeholder keys, API failures, metadata preservation, question validation, and real provider integration.
  - 10 tests passing with mocked LLM client, 1 integration test skipped when live key is unconfigured.
* **Known Limitations:**
  Requires a valid LLM API key (OpenAI, Groq, or local Ollama) in `.env` for live question answering. In the absence of an API key, the system provides safe, informative guidance while keeping retrieved passages available for inspection.

---

## 10. Module 5 Implementation Details

* **Implementation Files:** `modules/legal_analyzer.py`, `utils/prompts.py`, `app.py`, `utils/styles.py`
* **Technologies:** Python, OpenAI-compatible LLM client (Groq / OpenAI / local), FAISS Vector Retriever, JSON parsing & error fallback guards
* **Core Capabilities:**
  1. **Document Summary:**
     - Grounded executive summary covering: purpose & parties, main obligations, important dates/deadlines/payments, and termination/dispute terms.
     - Strict prompt constraint forbidding inference of absent facts.
     - Traceable to source document pages with supporting citations.
  2. **Important Clause Identification:**
     - Systematically classifies 9 standardized clause categories:
       1. Payment and compensation
       2. Termination and notice periods
       3. Confidentiality
       4. Liability and indemnification
       5. Penalties and damages
       6. Automatic renewal
       7. Intellectual property and ownership
       8. Rights and responsibilities of each party
       9. Governing law and dispute resolution
     - Returns: `category`, `explanation` (plain English), `quotation` (verbatim excerpt), `found` (boolean), `page_numbers` (list of integers), `source_file` (filename).
     - Explicit handling for missing categories: returns `"Not identified in the available text."` without assuming absence prematurely.
  3. **Potential Risk Identification:**
     - Flags ambiguous, one-sided, or onerous terms across 7 key areas: broad liability/indemnification, unclear payment terms, one-sided termination, automatic renewal traps, broad IP/confidentiality scope, ambiguous penalties, and missing dispute mechanisms.
     - Returns: `category`, `severity` (`Low`, `Medium`, `High`), `why_it_matters` (evidence-based explanation), `supporting_evidence` (quote), `page_reference`, `question_to_clarify` (practical question for user/counsel).
     - Strict rule: a clause is not labeled risky simply because it exists; severity is grounded in concrete document text.
  4. **Legal Disclaimer:**
     - Prominently embeds standard non-legal-advice disclaimer: output is for informational and educational review only, not binding legal counsel or an enforceability ruling.
* **Testing & Verification:**
  - `tests/test_legal_analyzer.py`: 10 comprehensive unit tests covering:
    - Summary generation with mocked responses
    - Clause extraction and structured schema validation
    - Risk identification and severity validation (`Low`/`Medium`/`High`)
    - Source and page metadata preservation
    - Insufficient evidence / empty document handling
    - Malformed and code-fenced JSON responses
    - Missing API key and provider failures
    - Documents where some clause categories are absent
    - Full orchestration via `analyze_legal_document`
  - Total test suite: **60 passed, 1 skipped** (live provider test).
* **Known Limitations:**
  - Analysis is bounded by the context window and retrieval chunk size; deeply buried sub-clauses in 100+ page contracts require multi-batch chunk aggregation.
  - LLM extraction quality depends on model capability; smaller local models may occasionally misclassify complex multi-layered covenants compared to frontier models.

---

## 11. Module 6 Implementation Details

* **Implementation Files:** `utils/report_generator.py`, `app.py`, `tests/test_report_generator.py`
* **Technologies:** Python, Streamlit native download buttons, Multi-format report serializers (Markdown, Plain Text, JSON)
* **Core Capabilities:**
  1. **Consolidated Report Export:**
     - Exports comprehensive legal report consolidating:
       - Header: Document filename, UTC analysis timestamp, and document metrics (pages, words, characters).
       - Mandatory Non-Legal-Advice Disclaimer.
       - Executive Document Summary with transactional dimensions (parties, purpose, obligations, dates/payments, termination/disputes) and cited pages.
       - 9-category Important Clause Inspection with status badges, explanations, verbatim quotations, and page references.
       - Potential Risk & Liability Audit with severity rankings (`[HIGH]`, `[MEDIUM]`, `[LOW]`), evidence quotes, page references, and practical counsel clarification questions.
  2. **Multi-Format Export Options:**
     - **Markdown (`.md`):** Formatted for legal review tools, documentation sites, GitHub, Obsidian, and Notion.
     - **Plain Text (`.txt`):** Pure ASCII layout with section dividers for raw viewing or email drafting.
     - **Structured JSON (`.json`):** Machine-readable payload for downstream legal tech workflows and audits.
  3. **Readiness & Completeness Tracking:**
     - Real-time status cards display whether Summary, Clauses, and Risks are Ready vs Pending.
     - Safely exports partial analyses without crashing, clearly annotating unexecuted sections.
     - Provides a one-click `Run Full Document Analysis Before Export` action directly within the export view.
  4. **Strict Privacy & Anti-Leakage:**
     - Scans and scrubs all export outputs: never outputs API keys, environment variables, or server paths.
  5. **State Management & Invalidation:**
     - Document changes immediately invalidate stale analysis results and chat history from prior documents.
     - Report downloads correspond strictly to the currently loaded document.
     - Avoids unnecessary FAISS index rebuilding during routine tab navigation or UI toggles.
* **Testing & Verification:**
  - `tests/test_report_generator.py`: 10 comprehensive unit tests covering:
    - Complete report generation in Markdown, Text, and JSON
    - Partial analysis handling (summary only, clauses only)
    - Unexecuted analysis handling without errors
    - Preservation of verbatim evidence quotes and exact page references
    - Safe handling of empty clause and risk lists
    - Zero secret/credential exposure verification
    - State invalidation and session reset on document change
  - Total test suite: **70 passed, 1 skipped** (live provider test).
* **Known Limitations:**
  - Reports are generated client-side from in-session state; multi-session persistent database history is out of scope.
  - PDF export is omitted to avoid heavy C-library dependencies (ReportLab / WeasyPrint); portable Markdown and text formats provide universal compatibility.

---

## 12. Final Six-Module Pipeline Architecture

```text
[PDF Upload] ──> [Module 1: PyMuPDF Extraction & Page Metadata]
                        │
                        ▼
                 [Module 2: LangChain Recursive Character Chunking]
                        │
                        ▼
                 [Module 3: SentenceTransformers Embeddings + FAISS Index]
                        │
                        ├──> [Module 4: Grounded RAG Q&A with Citations]
                        │
                        ├──> [Module 5: Executive Summary + 9 Clauses + Risk Audit]
                        │
                        └──> [Module 6: Final Results UI + Consolidated Report Export]
                                (Markdown, Plain Text, Structured JSON)
```

All six modules are fully implemented, verified, and integrated into the LegalLens application.

