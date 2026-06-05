"""Home page — landing page for the Podex dashboard."""

from pathlib import Path

import streamlit as st

# Get logo path
logo_path = Path(__file__).parent.parent / "static" / "podex-logo.svg"

# CSS only for centering the hero — Streamlit has no native text-align
st.markdown(
    """
    <style>
    .hero { text-align: center; padding: 2rem 0; }
    .hero-logo {
        display: flex; justify-content: center; align-items: center;
        gap: 1rem; margin-bottom: 1.5rem;
    }
    .hero-logo img { width: 120px; height: 120px; }
    /* Dark mode - make logo light to match text */
    @media (prefers-color-scheme: dark) {
        .hero-logo img {
            filter: grayscale(1) brightness(2.2) invert(1) !important;
        }
    }
    .hero-logo-text {
        font-size: 4rem !important; font-weight: 900 !important;
        letter-spacing: 0.1em; color: var(--text-color); margin: 0;
        text-transform: uppercase; line-height: 1;
    }
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
        <div class="hero-logo">
            <img src="app/static/podex-logo.svg" alt="Podex logo" />
            <p class="hero-logo-text">Podex</p>
        </div>
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
