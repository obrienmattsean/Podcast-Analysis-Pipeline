"""UI components and rendering functions for AI Search page."""

import logging
from typing import Any

import streamlit as st
from ai_search_config import SEARCH_PLACEHOLDER, SEARCH_SUGGESTIONS

logger = logging.getLogger(__name__)


def render_sidebar_settings() -> tuple[int, float, bool]:
    """Render sidebar settings and return configuration values.

    Returns:
        Tuple of (top_k, similarity_threshold, show_sources)
    """
    with st.sidebar:
        st.subheader("⚙️ Search Settings")

        top_k = st.slider(
            "Top K Results",
            min_value=5,
            max_value=50,
            value=15,
        )

        similarity_threshold = st.slider(
            "Similarity Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.50,
            step=0.05,
        )

        show_sources = st.checkbox(
            "Show Transcript Evidence",
            value=True,
        )

    return top_k, similarity_threshold, show_sources


def render_empty_state() -> tuple[str, bool]:
    """Render empty state with search input and suggestions.

    Returns:
        Tuple of (query, search_clicked)
    """
    st.markdown(
        """
        <div class="search-header">
            <h1>AI Search</h1>
            <p>Search across podcast transcripts using semantic retrieval.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "",
        placeholder=SEARCH_PLACEHOLDER,
        label_visibility="collapsed",
    )

    search_clicked = st.button(
        "✨ Search",
        use_container_width=True,
    )

    st.write("")

    cols = st.columns(2)

    suggestion_clicked = False
    suggestion_query = ""

    for i, suggestion in enumerate(SEARCH_SUGGESTIONS):
        with cols[i % 2]:
            if st.button(
                suggestion,
                use_container_width=True,
                key=f"suggestion_{i}",
            ):
                suggestion_clicked = True
                suggestion_query = suggestion

    return (
        suggestion_query if suggestion_clicked else query,
        search_clicked or suggestion_clicked,
    )


def render_search_header(query: str) -> str:
    """Render header with search input and button.

    Args:
        query: Current search query

    Returns:
        Updated query string
    """
    st.title("AI Search")

    col1, col2 = st.columns([8, 1])

    with col1:
        query = st.text_input(
            "",
            value=query,
            label_visibility="collapsed",
        )

    with col2:
        search_clicked = st.button("Search")

    return query, search_clicked


def render_summary_card(answer: str, num_episodes: int, num_podcasts: int) -> None:
    """Render summary card with AI response.

    Args:
        answer: LLM-generated answer
        num_episodes: Number of matching episodes
        num_podcasts: Number of matching podcasts
    """
    with st.container(border=True):
        st.caption("✨ PODEX AI SUMMARY")

        st.subheader(f"Found {num_episodes} matching episodes across {num_podcasts} podcasts")

        st.markdown(answer)

    st.write("")


def process_chunks(chunks: list[dict[str, Any]]) -> tuple[int, dict[tuple, dict]]:
    """Process chunks into organized episode structure.

    Args:
        chunks: List of chunk dictionaries from retrieval

    Returns:
        Tuple of (num_podcasts, episodes_dict)
    """
    podcasts: set[str] = set()
    episodes: dict[tuple[str, str], dict[str, Any]] = {}

    for chunk in chunks:
        podcast = chunk.get("podcast_title", "Unknown")
        episode = chunk.get("episode_title", "Unknown")

        podcasts.add(podcast)

        key = (podcast, episode)

        if key not in episodes:
            episodes[key] = {
                "podcast": podcast,
                "episode": episode,
                "count": 0,
                "chunks": [],
            }

        episodes[key]["count"] += 1
        episodes[key]["chunks"].append(chunk)

    return len(podcasts), episodes


def render_episode_cards(
    episodes: dict[tuple, dict],
    show_sources: bool,
) -> None:
    """Render episode cards with transcript evidence.

    Args:
        episodes: Dictionary of organized episodes
        show_sources: Whether to show transcript evidence
    """
    st.subheader(f"{len(episodes)} Matched Episodes")

    sorted_episodes = sorted(
        episodes.values(),
        key=lambda x: x["count"],
        reverse=True,
    )

    for episode in sorted_episodes:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(f"### 🎙️ {episode['podcast']}")
                st.caption(episode["episode"])

            with col2:
                st.metric(
                    "Mentions",
                    episode["count"],
                )

            if show_sources:
                with st.expander("Transcript Evidence"):
                    for chunk in episode["chunks"]:
                        similarity = chunk.get("similarity", 0)
                        st.caption(f"Similarity: {similarity:.2%}")
                        st.markdown(f"> {chunk['chunk_transcript']}")
                        st.divider()


def render_new_search_button() -> bool:
    """Render button to start new search.

    Returns:
        True if button clicked
    """
    st.write("")
    return st.button("← New Search")
