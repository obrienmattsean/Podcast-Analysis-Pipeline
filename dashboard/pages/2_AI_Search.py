"""AI Search page with RAG chatbot for semantic podcast search.

This page provides an interactive search interface powered by a Retrieval-Augmented
Generation (RAG) pipeline that searches podcast transcripts semantically.
"""

import logging

import streamlit as st
from ai_search_components import (
    process_chunks,
    render_empty_state,
    render_episode_cards,
    render_new_search_button,
    render_search_header,
    render_sidebar_settings,
    render_summary_card,
)
from ai_search_config import DEFAULT_SIMILARITY_THRESHOLD, DEFAULT_TOP_K, PAGE_CSS
from ai_search_utils import (
    clear_results,
    get_results,
    has_results,
    initialize_session_state,
    run_search,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AI Search",
    page_icon="🎙️",
    layout="wide",
)

st.markdown(PAGE_CSS, unsafe_allow_html=True)

# --------------------------------------------------
# INITIALIZATION
# --------------------------------------------------

initialize_session_state()

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

top_k, similarity_threshold, show_sources = render_sidebar_settings()

# --------------------------------------------------
# MAIN VIEW
# --------------------------------------------------

# Auto-run search when navigated from the home page search bar (must run
# before has_results() check so it fires even when old results are present)
if st.session_state.pop("_home_search_pending", False) and st.session_state.get("query"):
    run_search(st.session_state["query"], DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD)
    st.rerun()

if not has_results():
    # Empty state with search input
    query, search_clicked = render_empty_state()

    if search_clicked and query:
        run_search(query, top_k, similarity_threshold)
        st.rerun()

else:
    # Results view
    results = get_results()

    query, search_clicked = render_search_header(results["query"])

    if search_clicked and query:
        run_search(query, top_k, similarity_threshold)
        st.rerun()

    # Process and display results
    chunks = results["chunks"]
    num_podcasts, episodes = process_chunks(chunks)

    render_summary_card(results["answer"], len(episodes), num_podcasts)
    render_episode_cards(episodes, show_sources)

    if render_new_search_button():
        clear_results()
        st.rerun()
