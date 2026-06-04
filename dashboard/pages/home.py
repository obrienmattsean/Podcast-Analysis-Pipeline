"""Home page — landing page for the Podex dashboard."""

import streamlit as st

# CSS only for centering the hero — Streamlit has no native text-align
st.markdown(
    """
    <style>
    .hero { text-align: center; padding: 3.5rem 0 2rem; }
    .hero-wordmark {
        font-size: 0.75rem; letter-spacing: 0.2em; text-transform: uppercase;
        opacity: 0.4; color: var(--text-color); margin: 0 0 1.5rem;
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
        <div style="display:inline-flex;align-items:center;gap:1rem;margin-bottom:1.25rem;">
            <svg xmlns="http://www.w3.org/2000/svg" height="72" width="72"
                viewBox="0 0 239.5 239.5"
                style="opacity:0.85;flex-shrink:0;"
            ><path d="M239.5,120.8H0v-2h239.5V120.8z
                M120.8,0h-2v239.5h2V0z
                M205.2,203.8L35.8,34.4l-1.4,1.4l169.4,169.4 L205.2,203.8z
                M205.2,35.8l-1.4-1.4L34.4,203.8l1.4,1.4L205.2,35.8z
                M229,168.9L11.4,68.9l-0.8,1.8l217.7,100L229,168.9z
                M170.7,11.3l-1.8-0.8l-100,217.7l1.8,0.8L170.7,11.3z
                M162.3,231.7L79.1,7.1l-1.9,0.7l83.2,224.6L162.3,231.7z
                M232.4,79.1 l-0.7-1.9L7.1,160.4l0.7,1.9L232.4,79.1z"
            fill="currentColor"/></svg>
            <span class="hero-wordmark" style="margin:0;font-size:1.5rem;">PODEX</span>
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
            st.markdown("**Sentiment**")
            st.caption("Episode-level tone analysis")

    with col2:
        with st.container(border=True, height=100):
            st.markdown("**Keywords**")
            st.caption("Auto-extracted topics")

    with col3:
        with st.container(border=True, height=100):
            st.markdown("**AI Search**")
            st.caption("Semantic search across content")

    with col4:
        with st.container(border=True, height=100):
            st.markdown("**Brand Safety**")
            st.caption("Flag risky episodes early")
