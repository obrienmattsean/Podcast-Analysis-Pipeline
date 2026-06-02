"""Library page — displays all tracked podcasts as summary cards."""

import html

import streamlit as st
from db_functions import format_last_updated, get_all_podcasts, get_db_connection

_AVATAR_PALETTES: list[tuple[str, str]] = [
    ("#e8e0ff", "#5c3e9e"),
    ("#d0f0e8", "#1a6b50"),
    ("#fde8d0", "#8b4513"),
    ("#d8e8ff", "#1a4080"),
    ("#ffe0e8", "#8b1a3a"),
    ("#e8ffe0", "#2d6b1a"),
    ("#fff4d0", "#8b6914"),
    ("#f0d8ff", "#6b1a8b"),
]

_STOPWORDS: frozenset[str] = frozenset({"the", "a", "an", "of", "in", "on", "at", "to", "for"})


def get_podcast_initials(title: str) -> str:
    """Derive up-to-two-letter initials from a podcast title.

    Args:
        title: The podcast title.

    Returns:
        str: Uppercase initials, e.g. ``"MB"`` for ``"The Marketing Brew"``.

    Example:
        >>> get_podcast_initials("The Marketing Brew")
        'MB'
    """
    words = [w for w in title.split() if len(w) > 1 and w.lower() not in _STOPWORDS]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    if len(words) == 1:
        return words[0][:2].upper()
    return title[:2].upper()


def get_avatar_colors(title: str) -> tuple[str, str]:
    """Return a deterministic (background, text) color pair for a podcast avatar.

    Args:
        title: The podcast title used to seed the color selection.

    Returns:
        tuple[str, str]: A ``(background_color, text_color)`` pair as CSS hex strings.
    """
    idx = sum(ord(c) for c in title) % len(_AVATAR_PALETTES)
    return _AVATAR_PALETTES[idx]


def render_podcast_card(podcast: dict) -> None:
    """Render a styled summary card for a tracked podcast.

    Args:
        podcast: Dict with keys ``podcast_title``, ``num_episodes``,
            ``avg_sentiment_score``, and ``last_updated``.
    """
    title = podcast.get("podcast_title") or "Unknown Podcast"
    num_episodes = podcast.get("num_episodes") or 0
    avg_score = podcast.get("avg_sentiment_score")
    last_updated = podcast.get("last_updated")

    initials = get_podcast_initials(title)
    bg_color, text_color = get_avatar_colors(title)
    updated_text = f"Updated {format_last_updated(last_updated)}"

    if avg_score is not None:
        score = float(avg_score)
        if score > 0.5:
            dot_color, sentiment_label = "#4caf72", "Positive"
        elif score < -0.5:
            dot_color, sentiment_label = "#e57373", "Negative"
        else:
            dot_color, sentiment_label = "#888888", "Neutral"
        sentiment_html = (
            f'<div style="display:flex;align-items:center;gap:0.4rem;'
            f"font-size:0.85rem;color:{dot_color};font-weight:500;\">"
            f'<span style="width:8px;height:8px;border-radius:50%;background:{dot_color};'
            f'display:inline-block;flex-shrink:0;"></span>'
            f"{sentiment_label}</div>"
        )
    else:
        sentiment_html = ""

    st.markdown(
        f'<div style="background:var(--pod-secondary-bg);border:1px solid #2e2e2e;'
        f'border-radius:0.8rem;padding:1.25rem;margin-bottom:0.5rem;">'
        f'<div style="width:64px;height:64px;border-radius:12px;background:{bg_color};'
        f"display:flex;align-items:center;justify-content:center;"
        f'font-size:1.2rem;font-weight:700;color:{text_color};margin-bottom:1rem;">'
        f"{html.escape(initials)}"
        f"</div>"
        f'<div style="font-size:1.05rem;font-weight:700;color:var(--text-color);'
        f'margin-bottom:0.2rem;line-height:1.3;">{html.escape(title)}</div>'
        f'<div style="font-size:0.82rem;color:#888;margin-bottom:1rem;">'
        f"{html.escape(updated_text)}"
        f"</div>"
        f'<div style="display:flex;justify-content:space-between;align-items:flex-end;">'
        f"<div>"
        f'<div style="font-size:1.5rem;font-weight:700;color:var(--text-color);'
        f'line-height:1.2;">{html.escape(str(num_episodes))}</div>'
        f'<div style="font-size:0.78rem;color:#888;">episodes</div>'
        f"</div>"
        f"{sentiment_html}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_library() -> None:
    """Render the Library page showing all tracked podcasts as a two-column card grid."""
    conn = get_db_connection()
    podcasts = get_all_podcasts(conn)
    conn.close()

    if not podcasts:
        st.info("No podcasts tracked yet.")
        return

    st.markdown(
        f'<p style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;'
        f'color:#888;text-transform:uppercase;margin-bottom:1rem;">'
        f"{len(podcasts)} TRACKED PODCASTS</p>",
        unsafe_allow_html=True,
    )

    for i in range(0, len(podcasts), 2):
        cols = st.columns(2)
        with cols[0]:
            render_podcast_card(podcasts[i])
        if i + 1 < len(podcasts):
            with cols[1]:
                render_podcast_card(podcasts[i + 1])


render_library()
