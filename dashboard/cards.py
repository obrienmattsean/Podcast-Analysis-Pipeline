"""Reusable card components for episode and podcast display."""

import random
from typing import Literal

import streamlit as st
from db_functions import get_db_connection, get_flagged_categories_given_episode

_BadgeColor = Literal[
    "red", "orange", "yellow", "blue", "green", "violet", "gray", "grey", "primary"
]

_STOPWORDS: frozenset[str] = frozenset({"the", "a", "an", "of", "in", "on", "at", "to", "for"})


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


def _format_category_label(category: str) -> str:
    """Format unsafe category names for display.

    Args:
        category: Raw category key (e.g. ``self_harm_intent``).

    Returns:
        str: Human-friendly label (e.g. ``Self Harm Intent``).
    """
    return category.replace("_", " ").title()


def _build_badge_row(score: float | None, keywords: list[str]) -> str:
    """Build an HTML string of horizontally laid-out badge pills.

    Args:
        score: Sentiment score, or None to omit the sentiment pill.
        keywords: Keyword strings to render as blue pills.

    Returns:
        str: An HTML ``<div>`` containing inline ``<span>`` pill elements,
            or an empty string if there is nothing to render.
    """
    spans: list[str] = []
    if score is not None:
        label, color = _sentiment_label(float(score))
        hex_color = _SENTIMENT_COLOR_MAP.get(color, "#6c757d")
        spans.append(
            f'<span style="background-color:{hex_color};color:white;'
            f"padding:3px 10px;border-radius:12px;font-size:12px;"
            f'font-weight:600;margin-right:6px;">{label}</span>'
        )
    for kw in keywords:
        spans.append(
            f'<span style="background-color:#0d6efd;color:white;'
            f"padding:3px 10px;border-radius:12px;font-size:12px;"
            f'font-weight:600;margin-right:6px;">{kw.title()}</span>'
        )
    if not spans:
        return ""
    return '<div style="margin-bottom:6px;">' + "".join(spans) + "</div>"


def _resolve_flagged_categories(episode: dict) -> list[str]:
    """Resolve flagged categories from episode payload or database.

    Args:
        episode: Episode payload rendered by ``episode_card``.

    Returns:
        list[str]: Unsafe categories for the episode, if available.
    """
    payload_categories = episode.get("flagged_categories")
    if isinstance(payload_categories, list):
        return payload_categories

    episode_id = episode.get("episode_id")
    if episode_id is None:
        return []

    conn = get_db_connection()
    try:
        return get_flagged_categories_given_episode(conn, int(episode_id))
    finally:
        conn.close()


def _build_brand_safety_badge_html(
    brand_safe_color: str,
    brand_safe_label: str,
) -> str:
    """Build HTML for the brand safety badge.

    Args:
        brand_safe_color: Hex color for the badge background.
        brand_safe_label: Badge text label.

    Returns:
        str: HTML snippet for rendering the badge.
    """
    badge_style = (
        f"background-color:{brand_safe_color};color:white;padding:5px 12px;"
        "border-radius:14px;font-size:14px;font-weight:600;"
    )
    return f'<span style="{badge_style}">{brand_safe_label}</span>'


def episode_card(episode: dict) -> None:
    """Render a native Streamlit card for a single episode.

    Args:
        episode: Dict with keys ``episode_title``, ``podcast_title``,
            ``sentiment_score``, ``summary``, and ``time_since_published``.
    """
    episode_title = episode.get("episode_title") or "Untitled Episode"
    podcast_title = episode.get("podcast_title") or "Unknown Podcast"
    score = episode.get("sentiment_score")
    summary = episode.get("summary")
    time_since_published = episode.get("time_since_published") or ""
    brand_safe = not episode.get("flagged")
    keywords: list[str] = episode.get("keywords") or []
    brand_safe_color = "#28a745" if brand_safe else "#dc3545"
    brand_safe_label = "Brand Safe" if brand_safe else "Not Brand Safe"
    flagged_categories = _resolve_flagged_categories(episode) if not brand_safe else []

    with st.container(border=True):
        left, right = st.columns([4, 1], vertical_alignment="top")
        with left:
            left.caption(f":primary[**{podcast_title}**]")
            left.subheader(episode_title, anchor=False, divider=False)
            badge_html = _build_badge_row(score, random.sample(keywords, k=min(5, len(keywords))))
            if badge_html:
                left.markdown(badge_html, unsafe_allow_html=True)
        with right:
            right.markdown(
                f'<p style="text-align:right;margin:0;"><small>{time_since_published}</small></p>',
                unsafe_allow_html=True,
            )
            badge_html = _build_brand_safety_badge_html(
                brand_safe_color=brand_safe_color,
                brand_safe_label=brand_safe_label,
            )
            right.markdown(
                f'<p style="text-align:right;margin-top:8px;">{badge_html}</p>',
                unsafe_allow_html=True,
            )
            if not brand_safe:
                spacer_col, popover_col = right.columns([4, 1])
                with spacer_col:
                    st.empty()
                with popover_col:
                    with popover_col.popover(""):
                        if flagged_categories:
                            for category in sorted(set(flagged_categories)):
                                st.caption(f"• {_format_category_label(category)}")
                        else:
                            st.caption("Unsafe categories detected")
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
