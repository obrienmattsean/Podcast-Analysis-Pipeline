"Dashboard application using Streamlit to display recent podcast episodes from the database."

import html
from pathlib import Path

import streamlit as st
from db_functions import (
    get_db_connection,
    get_keywords_for_episode,
    get_recent_episodes,
    is_flagged_episode,
)

PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(page_title="Feed", layout="wide", initial_sidebar_state="expanded")

_secondary_bg = st.get_option("theme.secondaryBackgroundColor")
_primary_color = st.get_option("theme.primaryColor")

st.markdown(
    f"""
    <style>
    :root {{
        --pod-secondary-bg: {_secondary_bg};
        --pod-primary-color: {_primary_color};
    }}
    [data-testid="stSidebarNav"]::before {{
        content: "Podex AI";
        display: block;
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0.25rem 0 1rem 0;
        padding-left: 0.25rem;
        color: var(--pod-primary-color);
        letter-spacing: 0.01em;
    }}
    .episode-card {{
        background-color: var(--pod-secondary-bg);
        border: 1px solid #2e2e2e;
        border-radius: 0.6rem;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def get_sentiment_badge(score: float) -> str:
    """Return an HTML badge representing the sentiment score.

    Args:
        score: A float between -1.0 and 1.0 representing the sentiment score.

    Returns:
        str: An HTML string for a badge with color and label based on the score.
    """
    if score > 0.5:
        badge_color, text_color, label, emoji = "#1a3d22", "#4caf72", "Positive", "↗"
    elif score < -0.5:
        badge_color, text_color, label, emoji = "#3d1a1a", "#e57373", "Negative", "↘"
    else:
        badge_color, text_color, label, emoji = "#1a2a3d", "#7aadcf", "Neutral", "→"
    return (
        f'<span style="background:{badge_color};color:{text_color};padding:0.2rem 0.65rem;'
        f"border-radius:1rem;font-size:0.78rem;font-weight:600;white-space:nowrap;"
        f'border:1px solid {text_color}33;">'
        f"{emoji} {label}</span>"
    )


def render_episode_card(episode: dict) -> None:
    max_visible_keywords = 4

    episode_title = episode.get("episode_title", "Untitled Episode")
    podcast_title = episode.get("podcast_title", "Unknown Podcast")
    score = episode.get("sentiment_score")
    summary = episode.get("summary")
    audio_url = episode.get("audio_url")
    time_since_published = episode.get("time_since_published", "Unknown time")
    keywords: list[str] = episode.get("keywords", [])
    flagged: bool = episode.get("flagged", False)

    visible_keywords = keywords[:max_visible_keywords]
    remaining_keywords = keywords[max_visible_keywords:]

    badge_html = get_sentiment_badge(score) if score is not None else ""

    flag_html = (
        '<span style="background:#3d1a1a;color:#e57373;padding:0.2rem 0.65rem;'
        "border-radius:1rem;font-size:0.78rem;font-weight:600;white-space:nowrap;"
        'border:1px solid #e5737333;">'
        "⚑ Brand Risk</span>"
        if flagged
        else '<span style="background:#1a3d22;color:#4caf72;padding:0.2rem 0.65rem;'
        "border-radius:1rem;font-size:0.78rem;font-weight:600;white-space:nowrap;"
        'border:1px solid #4caf7233;">'
        "✓ Brand Safe</span>"
    )

    keyword_pills_html = "".join(
        f'<span style="background:#1e2a1e;color:#7aad8f;padding:0.15rem 0.55rem;'
        f"border-radius:1rem;font-size:0.75rem;font-weight:500;white-space:nowrap;"
        f'border:1px solid #7aad8f33;">{html.escape(kw)}</span>'
        for kw in visible_keywords
    )

    more_keywords_html = (
        f'<span style="color:#88a3b8;font-size:0.75rem;font-weight:600;'
        f'white-space:nowrap;">+{len(remaining_keywords)} more</span>'
        if remaining_keywords
        else ""
    )

    keywords_row_html = (
        f'<div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-top:0.6rem;">'
        f"{keyword_pills_html}</div>"
        f'<div style="margin-top:0.35rem;">{more_keywords_html}</div>'
        if visible_keywords
        else ""
    )

    summary_html = (
        f'<div style="font-size:0.85rem;color:var(--text-color);opacity:0.6;'
        f'line-height:1.55;margin-top:0.6rem;">'
        f"{html.escape(summary)}</div>"
        if summary
        else ""
    )

    has_audio_link = isinstance(audio_url, str) and audio_url.startswith(("http://", "https://"))
    listen_link_html = (
        '<a href="'
        f"{html.escape(audio_url, quote=True)}"
        '" target="_blank" rel="noopener noreferrer" '
        'style="font-size:0.8rem;font-weight:600;color:var(--pod-primary-color);'
        'text-decoration:none;">Listen Episode</a>'
        if has_audio_link
        else ""
    )

    st.markdown(
        f'<div class="episode-card">'
        f'  <div style="display:flex;justify-content:space-between;'
        f'align-items:baseline;margin-bottom:0.2rem;">'
        f'    <div style="font-size:0.78rem;color:var(--pod-primary-color);'
        f'font-weight:600;">{html.escape(podcast_title)}</div>'
        f'    <div style="font-size:0.78rem;color:var(--text-color);opacity:0.5;'
        f'white-space:nowrap;margin-left:1rem;">{html.escape(time_since_published)}</div>'
        f"  </div>"
        f'  <div style="font-size:1.05rem;font-weight:700;color:var(--text-color);'
        f'margin-bottom:0.5rem;line-height:1.35;">'
        f"    {html.escape(episode_title)}"
        f"  </div>"
        f'  <div style="margin-bottom:0.45rem;">{listen_link_html}</div>'
        f'  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;">'
        f"    {badge_html}"
        f"    {flag_html}"
        f"  </div>"
        f"  {keywords_row_html}"
        f"  {summary_html}"
        f"</div>",
        unsafe_allow_html=True,
    )

    if remaining_keywords:
        with st.expander("View all keywords"):
            full_keyword_pills_html = "".join(
                f'<span style="background:#1e2a1e;color:#7aad8f;padding:0.2rem 0.55rem;'
                f"border-radius:1rem;font-size:0.78rem;font-weight:500;"
                f'white-space:nowrap;border:1px solid #7aad8f33;">{html.escape(kw)}</span>'
                for kw in keywords
            )
            st.markdown(
                f'<div style="display:flex;gap:0.45rem;flex-wrap:wrap;">'
                f"{full_keyword_pills_html}</div>",
                unsafe_allow_html=True,
            )


def render_feed() -> None:
    """Render the feed page, showing recent episodes from the database.

    Returns:
        None: This function directly renders to the Streamlit app and does not return anything.
    """
    st.header("Feed")

    conn = get_db_connection()
    recent_episodes = get_recent_episodes(conn)
    for episode in recent_episodes:
        episode_id = episode.get("episode_id")
        if episode_id is not None:
            episode["keywords"] = get_keywords_for_episode(conn, episode_id)
            episode["flagged"] = is_flagged_episode(conn, episode_id)
    conn.close()

    for episode in recent_episodes:
        render_episode_card(episode)


navigation = st.navigation(
    [
        st.Page(render_feed, title="Feed", default=True),
        st.Page(str(PAGES_DIR / "1_Library.py"), title="Library"),
        st.Page(str(PAGES_DIR / "2_AI_Search.py"), title="AI Search"),
        st.Page(str(PAGES_DIR / "3_Settings.py"), title="Settings"),
    ],
    position="sidebar",
)

navigation.run()
