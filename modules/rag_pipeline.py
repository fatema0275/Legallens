"""
modules/rag_pipeline.py
Module 4: RAG Question Answering

Orchestrates Retrieval-Augmented Generation for legal document Q&A:
1. Validates user input questions.
2. Retrieves top-k relevant document chunks from the FAISS vector index (Module 3).
3. Constructs factually grounded prompts with strict anti-hallucination instructions (utils/prompts.py).
4. Invokes a configurable LLM provider API (OpenAI-compatible: OpenAI, Groq, local Ollama).
5. Returns plain-English answers with source citations and original evidence passages.
6. Handles missing API keys, API timeouts/failures, and insufficient evidence gracefully.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from utils.prompts import (
    INSUFFICIENT_EVIDENCE_PHRASE,
    build_rag_messages,
)
from modules.retriever import retrieve_relevant_chunks

# Ensure local .env file variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL_NAME = "gpt-3.5-turbo"
PLACEHOLDER_KEY_SUBSTRINGS = ["your_llm_api_key_here", "your_openai_api_key_here", "your_key_here"]


def get_llm_config(override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Resolves active LLM configuration from environment variables or runtime overrides.

    Parameters:
        override_config (Optional[Dict]): Runtime config dictionary with optional keys:
            - provider: "openai" | "groq" | "custom"
            - api_key: str
            - model_name: str
            - base_url: str

    Returns:
        Dict: Resolved configuration dictionary.
    """
    load_dotenv(override=True)
    config = dict(override_config or {})

    # Resolve provider
    provider = config.get("provider") or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).lower()

    # Resolve API Key
    api_key = config.get("api_key")
    if api_key is None:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or ""

    # Resolve Model Name
    model_name = config.get("model_name")
    if not model_name:
        default_model = "qwen/qwen3.8-27b" if provider == "groq" else DEFAULT_MODEL_NAME
        model_name = os.getenv("LLM_MODEL_NAME", default_model)

    # Resolve Base URL (e.g., for Groq or local Ollama)
    base_url = config.get("base_url")
    if not base_url:
        if provider == "groq":
            base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
        else:
            base_url = os.getenv("LLM_BASE_URL", None)

    return {
        "provider": provider,
        "api_key": api_key.strip() if isinstance(api_key, str) else "",
        "model_name": model_name,
        "base_url": base_url,
    }


def is_valid_api_key(api_key: Optional[str]) -> bool:
    """
    Checks if an API key is present and not a template placeholder.

    Parameters:
        api_key (Optional[str]): Key string to check.

    Returns:
        bool: True if key is non-empty and not a dummy placeholder.
    """
    if not api_key or not isinstance(api_key, str) or not api_key.strip():
        return False
    key_lower = api_key.strip().lower()
    for placeholder in PLACEHOLDER_KEY_SUBSTRINGS:
        if placeholder in key_lower:
            return False
    return True


def call_llm(
    messages: List[Dict[str, str]],
    config: Dict[str, Any],
    client_instance: Optional[object] = None,
) -> str:
    """
    Sends chat messages to the configured LLM API.

    Parameters:
        messages (List[Dict[str, str]]): System and user prompt messages.
        config (Dict[str, Any]): Resolved LLM configuration.
        client_instance: Optional injected client instance (used for mock testing).

    Returns:
        str: Generated plain-English answer.

    Raises:
        RuntimeError: If API call fails or client encounters an error.
    """
    # 1. Use injected client instance if provided (e.g. unit tests)
    if client_instance is not None:
        if hasattr(client_instance, "chat") and hasattr(client_instance.chat, "completions"):
            response = client_instance.chat.completions.create(
                model=config.get("model_name", DEFAULT_MODEL_NAME),
                messages=messages,
                temperature=0.0,
            )
            return response.choices[0].message.content
        elif callable(client_instance):
            return str(client_instance(messages))
        raise TypeError("Injected client_instance must have chat.completions.create or be callable.")

    # 2. Use OpenAI SDK client
    api_key = config.get("api_key", "")
    if not is_valid_api_key(api_key):
        raise ValueError(
            "Missing or placeholder LLM API key. Please set LLM_API_KEY in your .env file."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "The 'openai' package is required for Module 4 RAG Question Answering. "
            "Install it via: pip install openai"
        ) from exc

    client_kwargs = {"api_key": api_key}
    if config.get("base_url"):
        client_kwargs["base_url"] = config["base_url"]

    client = OpenAI(**client_kwargs)

    response = client.chat.completions.create(
        model=config.get("model_name", DEFAULT_MODEL_NAME),
        messages=messages,
        temperature=0.0,  # Zero temperature for deterministic, strictly grounded answers
    )

    content = response.choices[0].message.content
    return content.strip() if content else ""


def extract_citations(passages: List[Dict]) -> List[Dict[str, Any]]:
    """
    Extracts deduplicated source citations from retrieved passage dictionaries.

    Parameters:
        passages (List[Dict]): List of retrieved chunk dictionaries.

    Returns:
        List[Dict[str, Any]]: Ordered list of unique citation dicts [{'page_number': int, 'source': str}].
    """
    seen = set()
    citations = []
    for p in passages:
        p_num = p.get("page_number", 1)
        src = p.get("source", "document.pdf")
        key = (p_num, src)
        if key not in seen:
            seen.add(key)
            citations.append({"page_number": p_num, "source": src})
    return citations


def answer_question(
    question: str,
    retriever: Any,
    top_k: int = 3,
    llm_config: Optional[Dict[str, Any]] = None,
    client_instance: Optional[object] = None,
) -> Dict[str, Any]:
    """
    Executes the full RAG Question Answering pipeline:
    1. Validates the question.
    2. Retrieves top-k chunks from the FAISS retriever.
    3. Handles cases with no evidence or empty document.
    4. Validates API key configuration safely.
    5. Prompts the LLM with strict grounding constraints.
    6. Returns answer, supporting passages, and source page citations.

    Parameters:
        question (str): User question.
        retriever (Any): VectorRetriever instance or FAISS index bundle from Module 3.
        top_k (int): Number of passages to retrieve for grounding (default: 3).
        llm_config (Optional[Dict]): Runtime LLM configuration override.
        client_instance (Optional[object]): Injected mock LLM client for automated testing.

    Returns:
        Dict: Structured result dictionary containing:
            - answer (str): Grounded answer or clear error/insufficient evidence notice.
            - passages (List[Dict]): Retrieved chunks supporting the answer.
            - source_citations (List[Dict]): Formatted page citations.
            - has_evidence (bool): True if answer was derived from relevant passages.
            - success (bool): True if retrieval and LLM call completed successfully.
            - error (str or None): Error description if failure occurred.
            - model_name (str): LLM model used for generation.
    """
    # Step 1: Validate question
    if question is None or not isinstance(question, str):
        raise TypeError(f"Question must be a string, got: {type(question).__name__}")

    stripped_question = question.strip()
    if not stripped_question:
        raise ValueError("Question cannot be empty or whitespace-only.")

    # Step 2: Retrieve relevant passages using Module 3 retriever
    passages: List[Dict] = []
    try:
        passages = retrieve_relevant_chunks(
            query=stripped_question,
            retriever_or_index=retriever,
            top_k=top_k,
        )
    except Exception as exc:
        logger.error("Passage retrieval failed: %s", exc)
        return {
            "answer": f"Error retrieving document passages: {str(exc)}",
            "passages": [],
            "source_citations": [],
            "has_evidence": False,
            "success": False,
            "error": str(exc),
            "model_name": None,
        }

    citations = extract_citations(passages)

    # Step 3: Handle empty index / zero retrieved passages
    if not passages:
        return {
            "answer": INSUFFICIENT_EVIDENCE_PHRASE,
            "passages": [],
            "source_citations": [],
            "has_evidence": False,
            "success": True,
            "error": None,
            "model_name": None,
        }

    # Step 4: Resolve configuration and validate API key
    resolved_config = get_llm_config(override_config=llm_config)
    api_key = resolved_config.get("api_key", "")

    # If no client instance was injected and API key is missing, return safe guidance
    if client_instance is None and not is_valid_api_key(api_key):
        return {
            "answer": (
                "LLM API Key Not Configured: To generate answers, set your API key in the `.env` file "
                "(e.g., `LLM_API_KEY=your_key` or `OPENAI_API_KEY=your_key`). "
                "The retrieved evidence passages below remain available for inspection."
            ),
            "passages": passages,
            "source_citations": citations,
            "has_evidence": False,
            "success": False,
            "error": "Missing or placeholder LLM API key.",
            "model_name": resolved_config.get("model_name"),
        }

    # Step 5: Build chat messages payload
    messages = build_rag_messages(question=stripped_question, passages=passages)

    # Step 6: Invoke LLM
    try:
        raw_answer = call_llm(
            messages=messages,
            config=resolved_config,
            client_instance=client_instance,
        )

        # Step 7: Check if answer reflects insufficient evidence
        lower_ans = raw_answer.lower()
        has_evidence = not (
            "do not contain sufficient information" in lower_ans
            or "does not contain sufficient information" in lower_ans
            or "insufficient information" in lower_ans
            or "not enough information" in lower_ans
        )

        return {
            "answer": raw_answer,
            "passages": passages,
            "source_citations": citations,
            "has_evidence": has_evidence,
            "success": True,
            "error": None,
            "model_name": resolved_config.get("model_name"),
        }

    except Exception as exc:
        logger.error("LLM inference failed: %s", exc)
        return {
            "answer": f"Error generating answer from LLM: {str(exc)}",
            "passages": passages,
            "source_citations": citations,
            "has_evidence": False,
            "success": False,
            "error": str(exc),
            "model_name": resolved_config.get("model_name"),
        }
