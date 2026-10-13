# Legal Document Analyzer

A beginner-friendly educational prototype for analyzing legal documents (contracts, NDAs, service agreements) using Python, Streamlit, and Retrieval-Augmented Generation (RAG).

---

## Project Overview

Legal contracts are often dense, verbose, and difficult to comprehend. The **Legal Document Analyzer** is an educational application designed to bridge that gap through a grounded RAG pipeline:

1. **Module 1 (Completed):** PDF Processing — Document validation, page-by-page text extraction, metadata preservation (`page_number`, `source`, character and word metrics).
2. **Module 2 (Completed):** Text Chunking — Overlapping legal text chunking using LangChain splitters (`RecursiveCharacterTextSplitter`), page and source metadata preservation.
3. **Module 3 (Completed):** Embeddings & Retrieval — Sentence Transformers embedding generation (`all-MiniLM-L6-v2`) and local FAISS vector search (`IndexFlatIP`).
4. **Module 4 (Completed):** RAG Question Answering — Grounded Q&A with supporting passages, page citations, anti-hallucination prompts, and configurable LLM APIs.
5. **Module 5 (Completed):** Legal Document Analysis — Grounded executive summary, 9-category key clause detection with exact quotes & page citations, and review-priority risk audit (Low/Medium/High).
6. **Module 6 (Completed):** Results Interface & Report Export — Unified Streamlit dashboard, export status tracking, and downloadable analysis report in Markdown, Plain Text, and JSON.

> **Disclaimer:** This application is strictly an educational prototype and does not provide legal advice or definitive enforceability rulings.

---

## Project Structure

```text
legal-document-analyzer/
│
├── app.py                     # Streamlit web application interface
├── requirements.txt           # Active dependencies (Streamlit, PyMuPDF, LangChain, SentenceTransformers, FAISS, OpenAI)
├── README.md                  # Documentation and setup guide
├── PROJECT_CONTEXT.md         # Authoritative architectural specification
├── .env.example               # Environment variables template
├── .gitignore                 # Ignored files (venv, .env, cache)
├── test_pdf_extractor.py       # Test suite for Module 1 extraction & metadata
│
├── tests/
│   ├── test_text_chunker.py   # Test suite for Module 2 chunking (10 test cases)
│   ├── test_embeddings.py     # Test suite for Module 3 embeddings (8 test cases)
│   ├── test_retriever.py      # Test suite for Module 3 FAISS retriever (14 test cases)
│   ├── test_rag_pipeline.py   # Test suite for Module 4 RAG pipeline (11 test cases)
│   ├── test_legal_analyzer.py # Test suite for Module 5 Legal Analysis (11 test cases)
│   └── test_report_generator.py # Test suite for Module 6 Report Export (10 test cases)
│
├── modules/
│   ├── __init__.py
│   ├── pdf_processor.py       # [Module 1 - ACTIVE] PyMuPDF extraction & page metadata
│   ├── text_chunker.py        # [Module 2 - ACTIVE] LangChain recursive text chunking
│   ├── embeddings.py          # [Module 3 - ACTIVE] Sentence Transformers (all-MiniLM-L6-v2)
│   ├── retriever.py           # [Module 3 - ACTIVE] FAISS vector store & cosine retrieval
│   ├── rag_pipeline.py        # [Module 4 - ACTIVE] RAG Q&A orchestration & LLM API
│   └── legal_analyzer.py      # [Module 5 - ACTIVE] Executive summary, clauses & risk detection
│
├── utils/
│   ├── __init__.py
│   ├── prompts.py             # System & user prompt templates for grounded RAG and analysis
│   ├── styles.py              # Editorial design system, risk badges, and CSS tokens
│   ├── helpers.py             # Citation & formatting helpers
│   ├── charts.py              # Plotly chart visualizations for document statistics
│   └── report_generator.py    # [Module 6 - ACTIVE] Multi-format report export serializers
│
└── sample_documents/          # Directory for sample contracts and test PDFs
    ├── .gitkeep
    └── sample_contract.pdf
```

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ installed on your system.

### 2. Navigate to Project Directory
```powershell
cd c:\LegalLens\legal-document-analyzer
```

### 3. Set Up Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and specify your LLM credentials:
```powershell
cp .env.example .env
```
Supported providers include OpenAI (`LLM_PROVIDER=openai`), Groq fast tier (`LLM_PROVIDER=groq`), or local Ollama (`LLM_PROVIDER=custom`).

### 6. Launch the Application
```powershell
streamlit run app.py
```
The application will open in your default browser at `http://localhost:8501`.

---

## Testing & Verification

Run the complete test suite across all implemented modules:
```powershell
# Run all tests via pytest
.\venv\Scripts\python.exe -m pytest tests -v

# Or run individual module test suites:
.\venv\Scripts\python.exe test_pdf_extractor.py
.\venv\Scripts\python.exe -m pytest tests/test_text_chunker.py -v
.\venv\Scripts\python.exe -m pytest tests/test_embeddings.py -v
.\venv\Scripts\python.exe -m pytest tests/test_retriever.py -v
.\venv\Scripts\python.exe -m pytest tests/test_rag_pipeline.py -v
.\venv\Scripts\python.exe -m pytest tests/test_legal_analyzer.py -v
.\venv\Scripts\python.exe -m pytest tests/test_report_generator.py -v
```

Total test suite status: **70 passed, 1 skipped** (live provider test).

---

## Known Limitations
- **Scanned Documents:** Documents containing only scanned image scans without selectable text layers are detected and flagged with an informative notice. OCR is not implemented in this version.
- **Password-Protected Files:** Encrypted PDFs cannot be read and will prompt the user to provide an unencrypted version.
- **In-Memory FAISS Index:** FAISS vector stores are held in-memory per session; persistent multi-document indexing is deferred to future modules.
- **Long Document Batching:** For massive multi-hundred-page documents, clause classification relies on top-k semantic retrieval rather than full-context ingestion.
- **Non-Legal Advice:** Automated summaries, clause classifications, and risk indicators are strictly for educational review and issue spotting. They do not constitute binding legal counsel.
