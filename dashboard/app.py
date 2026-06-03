"Dashboard application using Streamlit to display recent podcast episodes from the database."

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Podex", layout="wide",
                   initial_sidebar_state="expanded")
st.logo(str(Path(__file__).parent / "static" / "podex-logo.svg"), size="large")

pages = [
    st.Page("pages/feed.py", title="Feed",
            icon=":material/dynamic_feed:", default=True),
    st.Page("pages/1_Library.py", title="Library",
            icon=":material/library_books:"),
    st.Page("pages/2_AI_Search.py", title="AI Search",
            icon=":material/search:"),
    st.Page("pages/3_Settings.py", title="Settings",
            icon=":material/settings:"),
    st.Page("pages/podcast_details.py", title="Podcast Analytics",
            icon=":material/analytics:"),
]

page = st.navigation(pages)


st.sidebar.page_link('pages/feed.py', label="Feed")
st.sidebar.page_link('pages/1_Library.py', label="Library")
st.sidebar.page_link('pages/2_AI_Search.py', label="AI Search")
st.sidebar.page_link('pages/3_Settings.py', label="Settings")
page.run()
