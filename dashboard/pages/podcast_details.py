"""Podcast details page — analytics view for a single tracked podcast."""

import streamlit as st
from db_functions import (
    format_last_updated,
    format_tracked_since,
    get_all_podcasts,
    get_db_connection,
)
from visualisation import render_keyword_bubble_chart

# ── Query params ────────────────────────────────────────────────────────────
podcast_title = st.query_params.get("podcast_title", "Unknown Podcast")
podcast_id = st.query_params.get("podcast_id")

# ── Back navigation ─────────────────────────────────────────────────────────
st.page_link("pages/1_Library.py", label="← Back to Library")

st.header(podcast_title)
st.divider()

# ── Stats row ───────────────────────────────────────────────────────────────
conn = get_db_connection()
podcasts = get_all_podcasts(conn)
podcast = next((p for p in podcasts if str(p.get("podcast_id")) == str(podcast_id)), None)

if podcast:
    avg_score = podcast.get("avg_sentiment_score")
    sentiment_display = f"{avg_score:+.2f}" if avg_score is not None else "N/A"

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Episodes", podcast.get("num_episodes", 0))
    m2.metric("Avg Sentiment", sentiment_display)
    m3.metric("Tracked Since", format_tracked_since(podcast.get("tracked_since")))
    m4.metric("Last Updated", format_last_updated(podcast.get("last_updated")))

    st.divider()

# ── Charts grid ─────────────────────────────────────────────────────────────
chart_col, spacer_col = st.columns([3, 2], gap="large")

with chart_col:
    st.subheader("Top Keywords")
    st.caption("Bubble size reflects how frequently each topic appears across episodes.")
    render_keyword_bubble_chart(conn, podcast_id)

with spacer_col:
    # Placeholder — additional charts (e.g. sentiment over time) can go here
    st.subheader("Coming Soon")
    st.caption("Sentiment trend and episode breakdown charts will appear here.")
