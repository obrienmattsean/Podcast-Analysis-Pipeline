"""Reusable card components for episode and podcast display."""

from typing import Literal

import streamlit as st

_BadgeColor = Literal[
    "red", "orange", "yellow", "blue", "green", "violet", "gray", "grey", "primary"
]

_STOPWORDS: frozenset[str] = frozenset({"the", "a", "an", "of", "in", "on", "at", "to", "for"})


def _brand_safety_label(score: int) -> tuple[str, str, str]:
    """Return (label, bg_color, text_color) for a brand safety score.

    Args:
        score: Brand safety score between 0 and 100.

    Returns:
        tuple[str, str, str]: A (label, bg_color, text_color) triple.
    """
    if score >= 70:
        return f"\U0001f6e1\ufe0f Brand safe \u00b7 {score}/100", "#dcfce7", "#166534"
    if score >= 40:
        return f"\U0001f6e1\ufe0f Brand safe \u00b7 {score}/100", "#fff3cd", "#856404"
    return f"\u26a0\ufe0f Unsafe \u00b7 {score}/100", "#f8d7da", "#842029"


def _sentiment_label(score: float) -> tuple[str, _BadgeColor]:
    """Return (label, badge_color) for a sentiment score.

    Args:
        score: Sentiment score between -1.0 and 1.0.

    Returns:
        tuple[str, str]: A (label, badge_color) pair where badge_color is a
            Streamlit-named color accepted by ``st.badge``.
    """
    if score > 0.5:
        return "↗ Positive", "green"
    if score < -0.5:
        return "↘ Negative", "red"
    return "→ Neutral", "gray"


def _podcast_initials(title: str) -> str:
    """Derive up-to-two-letter initials from a podcast title.

    Args:
        title: The podcast title.

    Returns:
        str: Uppercase initials.
    """
    words = [w for w in title.split() if len(w) > 1 and w.lower() not in _STOPWORDS]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    if len(words) == 1:
        return words[0][:2].upper()
    return title[:2].upper()


_SENTIMENT_COLOR_MAP: dict[str, str] = {
    "green": "#28a745",
    "red": "#dc3545",
    "gray": "#6c757d",
}


def _build_badge_row(score: float | None) -> str:
    """Build an HTML string of horizontally laid-out badge pills.

    Args:
        score: Sentiment score, or None to omit the sentiment pill.

    Returns:
        str: An HTML ``<div>`` containing inline ``<span>`` pill elements,
            or an empty string if there is nothing to render.
    """
    if score is None:
        return ""
    label, color = _sentiment_label(float(score))
    hex_color = _SENTIMENT_COLOR_MAP.get(color, "#6c757d")
    span = (
        f'<span style="background-color:{hex_color};color:white;'
        f"padding:3px 10px;border-radius:12px;font-size:12px;"
        f'font-weight:600;margin-right:6px;">{label}</span>'
    )
    return '<div style="margin-bottom:6px;">' + span + "</div>"


def episode_card(episode: dict) -> None:
    """Render a native Streamlit card for a single episode.

    Args:
        episode: Dict with keys ``episode_title``, ``podcast_title``,
            ``sentiment_score``, ``brand_safety_score``, ``summary``, and ``time_since_published``.
    """
    episode_title = episode.get("episode_title") or "Untitled Episode"
    podcast_title = episode.get("podcast_title") or "Unknown Podcast"
    score = episode.get("sentiment_score")
    brand_safety_score = episode.get("brand_safety_score")
    summary = episode.get("summary")
    time_since_published = episode.get("time_since_published") or ""

    with st.container(border=True):
        left, right = st.columns([4, 1], vertical_alignment="top")
        with left:
            left.caption(f":primary[**{podcast_title}**]")
            left.subheader(episode_title, anchor=False, divider=False)
            badge_html = _build_badge_row(score)
            if badge_html:
                left.markdown(badge_html, unsafe_allow_html=True)
        with right:
            right.markdown(
                f'<p style="text-align:right;margin:0;"><small>{time_since_published}</small></p>',
                unsafe_allow_html=True,
            )
            if brand_safety_score is not None:
                bs_label, bs_bg, bs_color = _brand_safety_label(int(brand_safety_score))
                right.markdown(
                    f'<p style="text-align:right;margin-top:8px;">'
                    f'<span style="background-color:{bs_bg};color:{bs_color};'
                    f'padding:5px 12px;border-radius:20px;font-size:13px;font-weight:600;">'
                    f"{bs_label}</span></p>",
                    unsafe_allow_html=True,
                )

        if summary:
            st.caption(summary)


def podcast_card(podcast: dict) -> None:
    """Render a native Streamlit card for a tracked podcast.

    Args:
        podcast: Dict with keys ``podcast_title``, ``num_episodes``,
            ``avg_sentiment_score``, and ``last_updated``.
    """
    title = podcast.get("podcast_title") or "Unknown Podcast"
    num_episodes = podcast.get("num_episodes") or 0
    avg_score = podcast.get("avg_sentiment_score")
    last_updated = podcast.get("last_updated") or ""

    initials = _podcast_initials(title)

    with st.container(border=True):
        st.subheader(f"{initials}  {title}", anchor=False)
        st.caption(f"Updated {last_updated}")
        st.divider()
        cols = st.columns(2)
        cols[0].metric("Episodes", num_episodes)
        if avg_score is not None:
            label, color = _sentiment_label(float(avg_score))
            cols[1].badge(label, color=color)
        st.page_link(
            "pages/podcast_details.py",
            label="View Analytics",
            use_container_width=True,
            icon=None,
            query_params={"podcast_title": title, "podcast_id": podcast.get("podcast_id")},
        )
