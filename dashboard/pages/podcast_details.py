import streamlit as st

return_button = st.page_link(
    "pages/1_Library.py", label="Return to Library", use_container_width=True)

podcast_title = st.query_params.get("podcast_title")
st.header(f"Analytics for {podcast_title}.")
