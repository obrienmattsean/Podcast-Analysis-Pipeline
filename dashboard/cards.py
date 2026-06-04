"""Reusable card components for episode and podcast display."""

from typing import Literal

import streamlit as st

_BadgeColor = Literal[
    "red", "orange", "yellow", "blue", "green", "violet", "gray", "grey", "primary"
]

_STOPWORDS: frozenset[str] = frozenset({"the", "a", "an", "of", "in", "on", "at", "to", "for"})


def _brand_safety_label(score: int) -> tuple[str, _BadgeColor]:
    """Return (label, badge_color) for a brand safety score.

    Args:
        score: Brand safety score between 0 and 100.

    Returns:
        tuple[str, _BadgeColor]: A (label, badge_color) pair.
    """
    if score >= 70:
        return f"\U0001f6e1\ufe0f Brand safe \u00b7 {score}/100", "green"
    if score >= 40:
        return f"\U0001f6e1\ufe0f Brand safe \u00b7 {score}/100", "orange"
    return f"\u26a0\ufe0f Unsafe \u00b7 {score}/100", "red"


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


def episode_card(episode: dict) -> None:
    episode_title = episode.get("episode_title") or "Untitled Episode"
    podcast_title = episode.get("podcast_title") or "Unknown Podcast"
    score = episode.get("sentiment_score")
    brand_safety_score = episode.get("brand_safety_score")
    summary = episode.get("summary")
    time_since_published = episode.get("time_since_published") or ""

    with st.container(border=True):
        left, sep, right = st.columns([5, 0.3, 1.5], vertical_alignment="center")

        with left:
            st.caption(f":primary[**{podcast_title}**]")
            st.subheader(episode_title, anchor=False, divider=False)
            if score is not None:
                sent_label, sent_color = _sentiment_label(float(score))
                st.badge(sent_label, color=sent_color)
            if summary:
                st.caption(summary)

        sep.markdown(
            '<div style="background-color:#dee2e6;width:2px;min-height:120px;margin:0 auto;"></div>',
            unsafe_allow_html=True,
        )

        with right:
            st.caption(time_since_published)
            if brand_safety_score is not None:
                bs_label, bs_color = _brand_safety_label(int(brand_safety_score))
                st.badge(bs_label, color=bs_color)


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
