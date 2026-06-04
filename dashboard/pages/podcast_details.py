"""Podcast details page — sentiment-over-time analytics for a single podcast."""

import pandas as pd
import streamlit as st
from db_functions import get_db_connection, get_episode_sentiment_for_podcast

st.page_link("pages/1_Library.py", label="← Return to Library")

podcast_title = st.query_params.get("podcast_title", "Unknown Podcast")
podcast_id = st.query_params.get("podcast_id")

st.header(f"Analytics: {podcast_title}")

if podcast_id is None:
    st.error("No podcast selected. Please return to the Library and click View Analytics.")
    st.stop()

conn = get_db_connection()
rows = get_episode_sentiment_for_podcast(conn, int(podcast_id))
conn.close()

scored_rows = [r for r in rows if r["sentiment_score"] is not None]

if not scored_rows:
    st.info("No sentiment data available yet for this podcast.")
    st.stop()

df = pd.DataFrame(scored_rows).set_index("pub_date")[["sentiment_score"]]
df.index = pd.to_datetime(df.index)
df = df.sort_index()

st.subheader("Sentiment Score Over Time")
st.line_chart(df, y="sentiment_score", x_label="Date", y_label="Sentiment Score")

