"""Library page — displays all tracked podcasts with episode statistics."""

import streamlit as st
from db_functions import format_tracked_since, get_all_podcasts, get_db_connection


def render_podcast_card(podcast: dict) -> None:
    """Render an expandable card for a tracked podcast.

    Clicking the card reveals episode count, tracking start date, and
    average sentiment score.

    Args:
        podcast: Dict with keys ``podcast_title``, ``num_episodes``,
            ``avg_sentiment_score``, and ``tracked_since``.
    """
    title = podcast.get("podcast_title") or "Unknown Podcast"
    num_episodes = podcast.get("num_episodes") or 0
    avg_score = podcast.get("avg_sentiment_score")
    tracked_since = podcast.get("tracked_since")

    with st.expander(title):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Episodes Tracked", num_episodes)
            st.caption(f"Since {format_tracked_since(tracked_since)}")
        with col2:
            score_display = f"{float(avg_score):+.2f}" if avg_score is not None else "N/A"
            st.metric("Avg Sentiment Score", score_display)


def render_library() -> None:
    """Render the Library page showing all tracked podcasts."""
    st.header("Library")

    conn = get_db_connection()
    podcasts = get_all_podcasts(conn)
    conn.close()

    if not podcasts:
        st.info("No podcasts tracked yet.")
        return

    for podcast in podcasts:
        render_podcast_card(podcast)


render_library()
