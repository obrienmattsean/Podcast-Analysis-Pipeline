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
        score = episode.get("sentiment_score")
        summary = episode.get("summary")

        if score is not None:
            if score >= 0.3:
                badge_color, label, emoji = "#1e7e34", "Positive", "▲"
            elif score <= -0.3:
                badge_color, label, emoji = "#c0392b", "Negative", "▼"
            else:
                badge_color, label, emoji = "#7f8c8d", "Neutral", "●"
            badge_html = (
                f'<div style="flex-shrink:0;text-align:center;">'
                f'<span style="background:{badge_color};color:#fff;padding:0.2rem 0.65rem;'
                f'border-radius:1rem;font-size:0.78rem;font-weight:600;white-space:nowrap;">'
                f'{emoji} {label}</span>'
                f'<div style="font-size:0.72rem;color:#888;margin-top:0.3rem;">{score:+.2f}</div>'
                f'</div>'
            )
        else:
            badge_html = ""

        summary_html = (
            f'<div style="font-size:0.9rem;color:#bbb;line-height:1.55;margin-top:0.5rem;">'
            f'{html.escape(summary)}</div>'
            if summary
            else ""
        )

        st.markdown(
            f'<div style="border:1px solid rgba(255,255,255,0.15);border-radius:0.5rem;'
            f'padding:1rem 1.25rem;margin-bottom:0.75rem;">'
            f'  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1.25rem;">'
            f'    <div style="flex:1;min-width:0;">'
            f'      <div style="font-size:1.05rem;font-weight:600;margin:0 0 0.15rem 0;">'
            f'        {html.escape(episode["episode_title"])}</div>'
            f'      <div style="font-size:0.78rem;color:#888;">'
            f'        {html.escape(episode["time_since_published"])}</div>'
            f'      {summary_html}'
            f'    </div>'
            f'    {badge_html}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )


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
