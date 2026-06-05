"""Reusable card components for episode and podcast display."""

from typing import Literal

import streamlit as st
from regex_expressions import remove_podcast_name

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

_AVATAR_PALETTE: list[tuple[str, str]] = [
    ("#dbeafe", "#1e40af"),
    ("#dcfce7", "#166534"),
    ("#fef9c3", "#854d0e"),
    ("#fce7f3", "#9d174d"),
    ("#ede9fe", "#4c1d95"),
    ("#ffedd5", "#9a3412"),
    ("#cffafe", "#155e75"),
    ("#f1f5f9", "#334155"),
]


def _avatar_colors(title: str) -> tuple[str, str]:
    """Return (bg, text) colors for an initials avatar derived from the title."""
    return _AVATAR_PALETTE[hash(title) % len(_AVATAR_PALETTE)]


def _initials_avatar_html(initials: str, bg: str, text_color: str, size: int = 40) -> str:
    """Return an HTML string for a circular initials avatar."""
    font_size = round(size * 0.38)
    return (
        f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
        f"background-color:{bg};display:inline-flex;align-items:center;"
        f"justify-content:center;font-size:{font_size}px;font-weight:700;"
        f'color:{text_color};flex-shrink:0;vertical-align:middle;">'
        f"{initials}</div>"
    )


def _sentiment_label(score: float) -> tuple[str, _BadgeColor]:
    """Return (label, badge_color) for a sentiment score.

    Args:
        score: Sentiment score between -1.0 and 1.0.

    Returns:
        _BadgeColor: A Streamlit-named color accepted by ``st.badge``.
    """
    if score > 0.5:
        return "green"
    if score < -0.5:
        return "red"
    return "gray"


def _sentiment_text(score: float) -> str:
    """Return human-friendly sentiment text for a score.

    Args:
        score: Sentiment score between -1.0 and 1.0.

    Returns:
        str: Sentiment direction and class text.
    """
    if score > 0.5:
        return "↗ Positive"
    if score < -0.5:
        return "↘ Negative"
    return "→ Neutral"


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

    remove_podcast_name(episode_title, podcast_title)

    initials = _podcast_initials(podcast_title)
    av_bg, av_text = _avatar_colors(podcast_title)
    avatar_html = _initials_avatar_html(initials, av_bg, av_text, size=28)

    with st.container(border=True):
        left, sep, right = st.columns([5, 0.3, 1.5], vertical_alignment="center")

        with left:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">'
                f"{avatar_html}"
                f'<span style="font-size:0.875rem;font-weight:600;">'
                f"{podcast_title}</span>"
                f'<span style="font-size:0.875rem;color:#6b7280;">· {time_since_published}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.subheader(episode_title, anchor=False, divider=False)
            if score is not None:
                sent_color = _sentiment_label(float(score))
                sent_label = _sentiment_text(float(score))
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
                    'align-items:center;margin-top:0.5rem;margin-bottom:0.5rem;">'
                    f"{sent_pill}{kw_pills}</div>",
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
            ``avg_sentiment_score``, ``historical_sentiment_score``, and ``last_updated``.
    """
    title = podcast.get("podcast_title") or "Unknown Podcast"
    num_episodes = podcast.get("num_episodes") or 0
    avg_score = podcast.get("avg_sentiment_score")
    historical_score = podcast.get("historical_sentiment_score")
    last_updated = podcast.get("last_updated") or ""

    initials = _podcast_initials(title)
    av_bg, av_text = _avatar_colors(title)
    avatar_html = _initials_avatar_html(initials, av_bg, av_text, size=48)
    with st.container(border=True):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">'
            f"{avatar_html}"
            f'<span style="font-size:1.25rem;font-weight:700;line-height:1.3;">{title}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Updated {last_updated}")
        st.divider()
        cols = st.columns(2)
        cols[0].metric("Episodes", num_episodes)
        if avg_score is not None:
            score_value = float(avg_score)
            score_text = f"{score_value:+.2f}"
            delta_text = None
            if historical_score is not None:
                delta_value = score_value - float(historical_score)
                delta_text = f"{delta_value:+.2f}"
            cols[1].metric(
                "Avg Sentiment",
                score_text,
                delta=delta_text,
                help="Shows the average sentiment score of top 5 most recent episodes. "
                "Delta shows the change between this average and the previous 5-episode average.",
            )
        st.page_link(
            "pages/podcast_details.py",
            label="View Analytics",
            use_container_width=True,
            icon=None,
            query_params={"podcast_title": title, "podcast_id": podcast.get("podcast_id")},
        )
