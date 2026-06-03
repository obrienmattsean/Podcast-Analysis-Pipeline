import streamlit as st

podcast_title = st.query_params.get("podcast_title")
st.header(f"Analytics for {podcast_title}.")
