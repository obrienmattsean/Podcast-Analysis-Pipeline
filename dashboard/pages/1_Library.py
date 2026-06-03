"""Library page — displays all tracked podcasts as summary cards."""

import streamlit as st
from cards import podcast_card
from db_functions import (
    format_last_updated,
    get_all_podcasts,
    get_db_connection,
    trigger_pipeline,
)

_RSS_ICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"'
    ' fill="none" stroke="#aaa" stroke-width="2.5" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<path d="M4 11a9 9 0 0 1 9 9"/>'
    '<path d="M4 4a16 16 0 0 1 16 16"/>'
    '<circle cx="5" cy="19" r="1" fill="#aaa" stroke="none"/>'
    "</svg>"
)


def render_add_rss_bar() -> None:
    """Render an inline bar for adding a new podcast by RSS URL."""
    label_html = (
        f'<div style="display:flex;align-items:center;gap:0.45rem;height:38px;'
        f'font-size:0.85rem;color:#aaa;white-space:nowrap;">'
        f"{_RSS_ICON_SVG}&nbsp;Add via RSS"
        f"</div>"
    )
    with st.form("add_rss_form", clear_on_submit=True):
        cols = st.columns([2, 8, 2])
        with cols[0]:
            st.markdown(label_html, unsafe_allow_html=True)
        with cols[1]:
            rss_url = st.text_input(
                "rss_url",
                placeholder="Paste RSS feed URL here...",
                label_visibility="collapsed",
            )
        with cols[2]:
            submitted = st.form_submit_button("Track", use_container_width=True)
    if submitted:
        url = rss_url.strip()
        if not url:
            st.warning("Please paste an RSS feed URL.")
        else:
            try:
                trigger_pipeline(url)
                st.success("Feed submitted for tracking.")
                st.rerun()
            except OSError as e:
                st.error(str(e))


def render_library() -> None:
    """Render the Library page showing all tracked podcasts as a two-column card grid."""
    render_add_rss_bar()

    conn = get_db_connection()
    podcasts = get_all_podcasts(conn)
    conn.close()

    if not podcasts:
        st.info("No podcasts tracked yet.")
        return

    st.markdown(
        f'<p style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;'
        f"color:color-mix(in srgb,var(--text-color) 55%,transparent);"
        f'text-transform:uppercase;margin-bottom:1rem;">'
        f"{len(podcasts)} TRACKED PODCASTS</p>",
        unsafe_allow_html=True,
    )

    for i in range(0, len(podcasts), 2):
        cols = st.columns(2)
        with cols[0]:
            p = dict(podcasts[i])
            p["last_updated"] = format_last_updated(p.get("last_updated"))
            podcast_card(p)
        if i + 1 < len(podcasts):
            with cols[1]:
                p = dict(podcasts[i + 1])
                p["last_updated"] = format_last_updated(p.get("last_updated"))
                podcast_card(p)


render_library()
