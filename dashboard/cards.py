"""Reusable card components for episode and podcast display."""

import streamlit as st

_STOPWORDS: frozenset[str] = frozenset({"the", "a", "an", "of", "in", "on", "at", "to", "for"})


def _sentiment_label(score: float) -> tuple[str, str]:
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

    with st.container(border=True):
        left, right = st.columns([4, 1], vertical_alignment="top")
        with left:
            st.caption(f":primary[**{podcast_title}**]")
            st.subheader(episode_title, anchor=False, divider=False)
        with right:
            st.markdown(
                f'<p style="text-align:right;margin:0;">'
                f'<small>{time_since_published}</small></p>',
                unsafe_allow_html=True,
            )
        if score is not None:
            label, color = _sentiment_label(float(score))
            st.badge(label, color=color)
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
