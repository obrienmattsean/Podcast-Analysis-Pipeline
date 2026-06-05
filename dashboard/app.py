"Dashboard application using Streamlit to display recent podcast episodes from the database."

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Podex", layout="wide", initial_sidebar_state="expanded")

# Toolbar logo - dark mode styling only
st.markdown(
    """
    <style>
    /* Dark mode for all logo instances */
    @media (prefers-color-scheme: dark) {
      .st-emotion-cache-1q56cwt img,
      .stSidebar img,
      aside img,
      nav img {
        filter: grayscale(1) brightness(2.2) invert(1) !important;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.logo(str(Path(__file__).parent / "static" / "podex-logo.svg"), size="large")

pages = [
    st.Page("pages/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("pages/feed.py", title="Feed", icon=":material/dynamic_feed:"),
    st.Page("pages/1_Library.py", title="Library", icon=":material/library_books:"),
    st.Page("pages/2_AI_Search.py", title="AI Search", icon=":material/search:"),
    st.Page("pages/3_Settings.py", title="Settings", icon=":material/settings:"),
    st.Page("pages/podcast_details.py", title="Podcast Details", icon=":material/podcasts:"),
]

page = st.navigation(pages)

st.sidebar.page_link("pages/home.py", label="Home")
st.sidebar.page_link("pages/feed.py", label="Feed")
st.sidebar.page_link("pages/1_Library.py", label="Library")
st.sidebar.page_link("pages/2_AI_Search.py", label="AI Search")
st.sidebar.page_link("pages/3_Settings.py", label="Settings")

page.run()
