"""Home page — landing page for the Podex dashboard."""

import streamlit as st

# CSS only for centering the hero — Streamlit has no native text-align
st.markdown(
    """
    <style>
    .hero { text-align: center; padding: 3.5rem 0 2rem; }
    .hero-wordmark {
        font-size: 3rem; letter-spacing: 0.2em; text-transform: uppercase;
        opacity: 0.6; color: var(--text-color); margin: 0 0 1.5rem;
        display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    }
    .hero-wordmark img { height: 120px; width: 120px; }
    .hero-title {
        font-size: 3rem; font-weight: 700; letter-spacing: -0.04em;
        line-height: 1.1; color: var(--text-color); margin: 0;
    }
    .feature-badge {
        display: inline-block;
        border: 1px solid var(--border-color, #d3d2ca);
        border-radius: 999px; padding: 0.25rem 0.9rem;
        font-size: 0.72rem; color: var(--text-color); opacity: 0.6;
    }
    .feature-badge-wrap { text-align: center; margin-bottom: 1.25rem; }
    </style>
    <div class="hero">
        <p class="hero-wordmark">
            <img src="app/static/podex-logo.svg" alt="Podex logo" />
            PODEX
        </p>
        <h1 class="hero-title">Understand every conversation.</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Search bar — main CTA
with st.form("home_search", border=False):
    _, search_col, btn_col, _ = st.columns([1, 5, 1, 1], vertical_alignment="bottom")
    with search_col:
        query = st.text_input(
            "search",
            placeholder="Search episodes, topics, guests...",
            label_visibility="collapsed",
        )
    with btn_col:
        go = st.form_submit_button(
            "Search", icon=":material/arrow_forward:", use_container_width=True
        )

_, status_col, _ = st.columns([1, 6, 1])
with status_col:
    status = st.empty()

if go and query:
    st.session_state["query"] = query
    st.session_state["_home_search_pending"] = True
    with status.status("Searching...", expanded=False):
        st.switch_page("pages/2_AI_Search.py")

st.write("")
st.write("")

# Feature section
st.markdown(
    '<div class="feature-badge-wrap"><span class="feature-badge">What\'s inside</span></div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown("### Your podcast library, finally making sense.")
    st.caption("Track shows, analyse sentiment, surface keywords and search episode content.")
    st.write("")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True, height=100):
            st.markdown("**Sentiment** — Tone scored per episode.")

    with col2:
        with st.container(border=True, height=100):
            st.markdown("**Keywords** — Top topics, auto-extracted.")

    with col3:
        with st.container(border=True, height=100):
            st.markdown("**AI Search** — Semantic search across all episodes.")

    with col4:
        with st.container(border=True, height=100):
            st.markdown("**Brand Safety** — Flag risky content before you commit.")
