"Dashboard application using Streamlit to display recent podcast episodes from the database."

from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Podex", layout="wide", initial_sidebar_state="expanded")
st.logo(str(Path(__file__).parent / "static" / "podex-logo.svg"), size="large")

pages = [
    st.Page("pages/feed.py", title="Feed", icon=":material/dynamic_feed:", default=True),
    st.Page("pages/1_Library.py", title="Library", icon=":material/library_books:"),
    st.Page("pages/2_AI_Search.py", title="AI Search", icon=":material/search:"),
    st.Page("pages/3_Settings.py", title="Settings", icon=":material/settings:"),
]

page = st.navigation(pages)
page.run()

