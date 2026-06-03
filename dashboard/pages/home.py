"""Home page — landing page for the Podex dashboard."""

import streamlit as st

# CSS only for centering the hero — Streamlit has no native text-align
st.markdown(
    """
    <style>
    .hero { text-align: center; padding: 3.5rem 0 2rem; }
    .hero-wordmark { font-size: 0.75rem; letter-spacing: 0.2em; text-transform: uppercase; opacity: 0.4; color: var(--text-color); margin: 0 0 1.5rem; }
    .hero-title { font-size: 3rem; font-weight: 700; letter-spacing: -0.04em; line-height: 1.1; color: var(--text-color); margin: 0; }
    .feature-badge { display: inline-block; border: 1px solid var(--border-color, #d3d2ca); border-radius: 999px; padding: 0.25rem 0.9rem; font-size: 0.72rem; color: var(--text-color); opacity: 0.6; }
    .feature-badge-wrap { text-align: center; margin-bottom: 1.25rem; }
    </style>
    <div class="hero">
        <p class="hero-wordmark">✦ &nbsp; PODEX &nbsp; ✦</p>
        <h1 class="hero-title">Your podcast intelligence,<br>all in one place.</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Search bar — main CTA
_, search_col, btn_col, _ = st.columns([1, 5, 1, 1], vertical_alignment="bottom")
with search_col:
    query = st.text_input(
        "search",
        placeholder="Search episodes, topics, guests...",
        label_visibility="collapsed",
    )
with btn_col:
    go = st.button("Search", icon=":material/arrow_forward:", use_container_width=True)

if go and query:
    st.session_state["ai_search_query"] = query
    st.switch_page("pages/2_AI_Search.py")

st.write("")
st.write("")

# Feature section
st.markdown(
    '<div class="feature-badge-wrap"><span class="feature-badge">What\'s inside</span></div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown("### Understand every episode, at a glance.")
    st.caption(
        "Track shows, analyse sentiment, surface keywords and search episode content."
    )
    st.write("")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True, height=100):
            st.markdown("**Sentiment**")
            st.caption("Episode-level tone analysis")

    with col2:
        with st.container(border=True, height=100):
            st.markdown("**Keywords**")
            st.caption("Top topics extracted automatically")

    with col3:
        with st.container(border=True, height=100):
            st.markdown("**AI Search**")
            st.caption("Semantic search across content")

    with col4:
        with st.container(border=True, height=100):
            st.markdown("**Brand Safety**")
            st.caption("Flag episodes before committing budget")



