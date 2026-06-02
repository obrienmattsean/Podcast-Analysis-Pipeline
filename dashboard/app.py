"Dashboard application using Streamlit to display recent podcast episodes from the database."

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
        with st.container(border=True):
            st.subheader(episode["title"])
            st.caption(f"{episode['podcast_title']} | {episode['days_since_published']} days ago")

        st.write("")


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
