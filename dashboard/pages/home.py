"""Home page — landing page for the Podex dashboard."""

import streamlit as st

st.title("PODEX")
st.caption("✦ AI PODCAST INTELLIGENCE")

st.markdown("## Understand every episode, at a glance")
st.markdown(
    "Track shows, analyse sentiment, surface keywords and search episode content — powered by AI."
)

st.divider()

_, cta_left, cta_right, _ = st.columns([2, 1, 1, 2])
with cta_left:
    st.page_link(
        "pages/1_Library.py",
        label="Add a Podcast",
        icon=":material/library_books:",
        use_container_width=True,
    )
with cta_right:
    st.page_link(
        "pages/2_AI_Search.py",
        label="Search Episodes",
        icon=":material/search:",
        use_container_width=True,
    )

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("🎙 **Sentiment**")
    st.caption("Episode-level tone analysis from transcripts")

with col2:
    st.markdown("🏷 **Keywords**")
    st.caption("Top topics extracted automatically")

with col3:
    st.markdown("🔍 **AI Search**")
    st.caption("Semantic search across all episode content")

with col4:
    st.markdown("🛡 **Brand Safety**")
    st.caption("Flag episodes before you commit budget")
