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


_BRAND_SAFETY_COLOR_MAP: dict[str, tuple[str, str]] = {
    "green": ("#dcfce7", "#166534"),
    "orange": ("#fff3cd", "#856404"),
    "red": ("#f8d7da", "#842029"),
}

_SENTIMENT_COLOR_MAP: dict[str, tuple[str, str]] = {
    "green": ("#dcfce7", "#166534"),
    "red": ("#f8d7da", "#842029"),
    "gray": ("#e9ecef", "#495057"),
}


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
    keywords = episode.get("keywords", [])
    time_since_published = episode.get("time_since_published") or ""

    with st.container(border=True):
        left, sep, right = st.columns([5, 0.3, 1.5], vertical_alignment="center")

        with left:
            st.caption(f":primary[**{podcast_title}**] :gray[· {time_since_published}]")
            st.subheader(episode_title, anchor=False, divider=False)
            if score is not None:
                sent_label, sent_color = _sentiment_label(float(score))
                sent_bg, sent_text = _SENTIMENT_COLOR_MAP[sent_color]
                _pill = (
                    "padding:4px 10px;border-radius:12px;"
                    "font-size:0.82rem;font-weight:600;white-space:nowrap;"
                )
                sent_pill = (
                    f'<span style="background-color:{sent_bg};color:{sent_text};{_pill}">'
                    f"{sent_label}</span>"
                )
                kw_pills = "".join(
                    f'<span style="background-color:#dbeafe;color:#1e40af;{_pill}">{kw}</span>'
                    for kw in (keywords or [])[:5]
                )
                st.markdown(
                    '<div style="display:flex;flex-wrap:wrap;gap:6px;'
                    f'align-items:center;">{sent_pill}{kw_pills}</div>',
                    unsafe_allow_html=True,
                )
            if summary:
                st.caption(summary)

        sep.markdown(
            '<div style="background-color:#dee2e6;width:2px;min-height:120px;'
            'margin:0 auto;"></div>',
            unsafe_allow_html=True,
        )

        with right:
            if brand_safety_score is not None:
                bs_label, bs_color = _brand_safety_label(int(brand_safety_score))
                bs_bg, bs_text = _BRAND_SAFETY_COLOR_MAP[bs_color]
                st.markdown(
                    f'<span style="background-color:{bs_bg};color:{bs_text};'
                    f'padding:8px 14px;border-radius:20px;font-size:1rem;font-weight:700;">'
                    f"{bs_label}</span>",
                    unsafe_allow_html=True,
                )


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
