"Dashboard application using Streamlit to display recent podcast episodes from the database."

import html
from pathlib import Path

import streamlit as st
from db_functions import get_db_connection, get_recent_episodes

PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(page_title="Feed", layout="wide", initial_sidebar_state="expanded")
st.logo(str(Path(__file__).parent / "static" / "podex-logo.svg"), size="large")

_secondary_bg = st.get_option("theme.secondaryBackgroundColor")
_primary_color = st.get_option("theme.primaryColor")

st.markdown(
    f"""
    <style>
    :root {{
        --pod-secondary-bg: {_secondary_bg};
        --pod-primary-color: {_primary_color};
    }}
    @font-face {{
        font-family: "TT Commons Pro";
        src: url("app/static/fonts/Demo_Fonts/Fontspring-DEMO-tt_commons_pro_regular.otf") format("opentype");
        font-weight: 400;
        font-style: normal;
    }}
    @font-face {{
        font-family: "TT Commons Pro";
        src: url("app/static/fonts/Demo_Fonts/Fontspring-DEMO-tt_commons_pro_italic.otf") format("opentype");
        font-weight: 400;
        font-style: italic;
    }}
    @font-face {{
        font-family: "TT Commons Pro";
        src: url("app/static/fonts/Demo_Fonts/Fontspring-DEMO-tt_commons_pro_medium.otf") format("opentype");
        font-weight: 500;
        font-style: normal;
    }}
    @font-face {{
        font-family: "TT Commons Pro";
        src: url("app/static/fonts/Demo_Fonts/Fontspring-DEMO-tt_commons_pro_demibold.otf") format("opentype");
        font-weight: 600;
        font-style: normal;
    }}
    @font-face {{
        font-family: "TT Commons Pro";
        src: url("app/static/fonts/Demo_Fonts/Fontspring-DEMO-tt_commons_pro_bold.otf") format("opentype");
        font-weight: 700;
        font-style: normal;
    }}
    html, body, [class*="css"] {{
        font-family: "TT Commons Pro", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    [data-testid="stAppViewContainer"] {{
        background:
            radial-gradient(ellipse at 72% 18%, rgba(196, 178, 227, 0.38) 0%, transparent 52%),
            radial-gradient(ellipse at 18% 82%, rgba(255, 195, 180, 0.22) 0%, transparent 48%),
            radial-gradient(ellipse at 48% 58%, rgba(180, 210, 240, 0.18) 0%, transparent 46%),
            #f0ece3;
    }}
    [data-testid="stHeader"] {{
        background: transparent;
        box-shadow: none;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(244, 241, 233, 0.72);
        backdrop-filter: blur(20px) saturate(1.6);
        -webkit-backdrop-filter: blur(20px) saturate(1.6);
        border-right: 1px solid rgba(0, 0, 0, 0.06);
    }}
    [data-testid="stLogo"] {{
        display: flex;
        justify-content: center;
        width: 100%;
        padding: 1rem 0;
    }}
    [data-testid="stLogo"] img {{
        width: 160px !important;
        max-height: none !important;
        height: auto;
        filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
    }}
    h1, h2, h3 {{
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    .episode-card {{
        background: rgba(255, 255, 255, 0.55);
        border: none;
        border-radius: 1rem;
        padding: 1.1rem 1.4rem;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(12px) saturate(1.4);
        -webkit-backdrop-filter: blur(12px) saturate(1.4);
        box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: box-shadow 0.2s ease;
    }}
    .episode-card:hover {{
        box-shadow: 0 6px 28px rgba(0, 0, 0, 0.1), 0 2px 6px rgba(0, 0, 0, 0.06);
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
        badge_color, text_color, label, emoji = "rgba(52,199,89,0.12)", "#1a8035", "Positive", "↗"
    elif score < -0.5:
        badge_color, text_color, label, emoji = "rgba(255,59,48,0.10)", "#c0392b", "Negative", "↘"
    else:
        badge_color, text_color, label, emoji = "rgba(142,142,147,0.14)", "#636366", "Neutral", "→"
    return (
        f'<span style="background:{badge_color};color:{text_color};padding:0.2rem 0.65rem;'
        f"border-radius:2rem;font-size:0.75rem;font-weight:500;white-space:nowrap;"
        f'letter-spacing:0.01em;">'
        f"{emoji} {label}</span>"
    )


def render_episode_card(episode: dict) -> None:
    episode_title = episode.get("episode_title", "Untitled Episode")
    podcast_title = episode.get("podcast_title", "Unknown Podcast")
    score = episode.get("sentiment_score")
    summary = episode.get("summary")
    time_since_published = episode.get("time_since_published", "Unknown time")

    badge_html = get_sentiment_badge(score) if score is not None else ""

    summary_html = (
        f'<div style="font-size:0.85rem;color:var(--text-color);opacity:0.6;'
        f'line-height:1.55;margin-top:0.6rem;">'
        f"{html.escape(summary)}</div>"
        if summary
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
        f'  <div style="display:flex;gap:0.5rem;flex-wrap:wrap;">'
        f"    {badge_html}"
        f"  </div>"
        f"  {summary_html}"
        f"</div>",
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
