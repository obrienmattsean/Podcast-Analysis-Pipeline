"""Podcast details page — sentiment-over-time analytics for a single podcast."""

import altair as alt
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

df = pd.DataFrame(scored_rows)
df["pub_date"] = pd.to_datetime(df["pub_date"])
df = df.sort_values("pub_date")

st.subheader("Sentiment Score Over Time")
chart = (
    alt.Chart(df.reset_index())
    .mark_line(point=True)
    .encode(
        x=alt.X("pub_date:T", title="Date"),
        y=alt.Y(
            "sentiment_score:Q",
            title="Sentiment Score",
            scale=alt.Scale(domain=[-1, 1]),
        ),
        tooltip=["episode_title:N", "pub_date:T", "sentiment_score:Q"],
    )
    .properties(width="container")
    .interactive()
)
st.altair_chart(chart, use_container_width=True)

