"""Utilities and search logic for AI Search page."""

import logging
from typing import Any

import streamlit as st
from rag.convert import get_openai_client, get_query_embedding
from rag.generator import answer_query
from rag.retrieval import get_db_connection, query_similar_chunks

logger = logging.getLogger(__name__)


def initialize_session_state() -> None:
    """Initialize session state variables if not already set."""
    if "results" not in st.session_state:
        st.session_state.results = None

    if "query" not in st.session_state:
        st.session_state.query = ""


def run_search(query: str, top_k: int, similarity_threshold: float) -> None:
    """Execute search and store results in session state.

    Args:
        query: Search query string
        top_k: Number of top results to retrieve
        similarity_threshold: Minimum similarity score for results

    Raises:
        Exception: If search fails
    """
    try:
        with st.spinner("Searching podcast transcripts..."):
            # Generate answer using RAG pipeline
            answer = answer_query(
                user_query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
            )

            # Retrieve chunks for display
            openai_client = get_openai_client()
            db_conn = get_db_connection()

            try:
                embedding = get_query_embedding(openai_client, query)

                chunks = query_similar_chunks(
                    db_conn,
                    embedding,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold,
                )

                st.session_state.results = {
                    "query": query,
                    "answer": answer,
                    "chunks": chunks,
                }

                logger.info(
                    "Search completed: %d chunks retrieved for query: %s",
                    len(chunks),
                    query,
                )

            finally:
                db_conn.close()

    except ValueError as e:
        st.error(f"Configuration Error: {str(e)}")
        logger.error("Configuration error during search: %s", str(e))

    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        logger.error("Search failed with error: %s", str(e))


def clear_results() -> None:
    """Clear search results and reset session state."""
    st.session_state.results = None
    st.session_state.query = ""


def has_results() -> bool:
    """Check if search results are available.

    Returns:
        True if results exist in session state
    """
    return st.session_state.results is not None


def get_results() -> dict[str, Any]:
    """Get current search results.

    Returns:
        Dictionary containing query, answer, and chunks
    """
    return st.session_state.results or {}
