"Dashboard application using Streamlit to display recent podcast episodes from the database."

import html
from pathlib import Path

import streamlit as st
from db_functions import get_db_connection, get_recent_episodes

PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(page_title="Feed", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"]::before {
        content: "Podex AI";
        display: block;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0.25rem 0 1rem 0;
        padding-left: 0.25rem;
        color: #e55f15;
        letter-spacing: 0.01em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_sentiment_badge(score: float) -> str:
    """Return an HTML badge representing the sentiment score.

    Args:
        score: A float between -1.0 and 1.0 representing the sentiment score.

    Returns:
        str: An HTML string for a badge with color and label based on the score.
    """
    if score >= 0.3:
        badge_color, text_color, label, emoji = "#1a3d22", "#4caf72", "Positive", "↗"
    elif score <= -0.3:
        badge_color, text_color, label, emoji = "#3d1a1a", "#e57373", "Negative", "↘"
    else:
        badge_color, text_color, label, emoji = "#2a2a2a", "#aaa", "Neutral", "→"
    return (
        f'<span style="background:{badge_color};color:{text_color};padding:0.2rem 0.65rem;'
        f'border-radius:1rem;font-size:0.78rem;font-weight:600;white-space:nowrap;'
        f'border:1px solid {text_color}33;">'
        f"{emoji} {label}</span>"
    )


def render_episode_card(episode: dict) -> None:
    episode_title = episode.get("episode_title", "Untitled Episode")
    podcast_title = episode.get("podcast_title", "Unknown Podcast")
    score = episode.get("sentiment_score")
    summary = episode.get("summary")
    time_since_published = episode.get("time_since_published", "Unknown time")

    badge_html = get_sentiment_badge(score) if score is not None else ""

    summary_html = (
        f'<div style="font-size:0.85rem;color:#999;line-height:1.55;margin-top:0.6rem;">'
        f"{html.escape(summary)}</div>"
        if summary
        else ""
    )

    st.markdown(
        f'<div style="border:1px solid rgba(255,255,255,0.12);border-radius:0.6rem;'
        f'padding:1rem 1.25rem;margin-bottom:0.75rem;">'
        f'  <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0.2rem;">'
        f'    <div style="font-size:0.78rem;color:#e55f15;font-weight:600;">{html.escape(podcast_title)}</div>'
        f'    <div style="font-size:0.78rem;color:#888;white-space:nowrap;margin-left:1rem;">{html.escape(time_since_published)}</div>'
        f'  </div>'
        f'  <div style="font-size:1.05rem;font-weight:700;color:#f0f0f0;margin-bottom:0.5rem;line-height:1.35;">'
        f'    {html.escape(episode_title)}'
        f'  </div>'
        f'  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">'
        f'    {badge_html}'
        f'  </div>'
        f'  {summary_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_feed() -> None:
    """Render the feed page, showing recent episodes from the database.

    Returns:
        None: This function directly renders to the Streamlit app and does not return anything.
    """
    st.header("Feed")

    conn = get_db_connection()
    recent_episodes = get_recent_episodes(conn)
    conn.close()

    for episode in recent_episodes:
        render_episode_card(episode)


navigation = st.navigation(
    [
        st.Page(render_feed, title="Feed", default=True),
        st.Page(str(PAGES_DIR / "1_Library.py"), title="Library"),
        st.Page(str(PAGES_DIR / "2_AI_Search.py"), title="AI Search"),
        st.Page(str(PAGES_DIR / "3_Settings.py"), title="Settings"),
    ],
    position="sidebar",
)

navigation.run()
