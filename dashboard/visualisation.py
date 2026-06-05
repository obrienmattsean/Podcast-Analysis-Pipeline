"""Visualization components for podcast analysis dashboard."""

import textwrap

import altair as alt
import circlify
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from db_functions import get_keywords_for_podcast, get_sentiment_over_time
from psycopg2.extensions import connection

# Colours taken directly from .streamlit/config.toml
# primaryColor, chartCategoricalColors, textColor and their tonal derivatives
_BG_COLOR = "#fdfdf8"  # theme.backgroundColor
_BUBBLE_PALETTE = [
    "#cb785c",  # primaryColor
    "#0ea5e9",  # chartCategoricalColors[0] — sky blue
    "#059669",  # chartCategoricalColors[1] — emerald
    "#fbbf24",  # chartCategoricalColors[2] — amber
    "#b85f3f",  # primaryColor darkened
    "#0284c7",  # sky blue darkened
    "#047857",  # emerald darkened
    "#d97706",  # amber darkened
    "#d4956e",  # primaryColor lightened
    "#38bdf8",  # sky blue lightened
]
# Matches [theme].font in .streamlit/config.toml
_DASHBOARD_FONT_FAMILY = "SpaceGrotesk"


def _fit_bubble_label(label: str, radius: float) -> tuple[str, int]:
    """Wrap and size a label so it fits inside a bubble.

    Args:
        label: Raw keyword label text.
        radius: Bubble radius from circlify.

    Returns:
        tuple[str, int]: Wrapped label text and a font size.
    """
    # Base font is explicitly tied to bubble radius (diameter-driven).
    # Larger bubbles should clearly get larger labels.
    diameter = radius * 2
    start_font_size = max(5, min(16, int(diameter * 14)))

    # Find the largest font that allows wrapped text to fit without mid-word truncation.
    for font_size in range(start_font_size, 4, -1):
        scale = start_font_size / font_size
        chars_per_line = max(4, int(diameter * 12 * scale))
        max_lines = max(1, int(diameter * 6 * scale))
        wrapped_lines = textwrap.wrap(label, width=chars_per_line, break_long_words=False)

        if not wrapped_lines:
            wrapped_lines = [label]
        if len(wrapped_lines) > max_lines:
            continue

        wrapped_label = "\n".join(wrapped_lines)
        return wrapped_label, font_size

    # Final fallback for extremely small bubbles or long unbroken tokens.
    fallback_lines = textwrap.wrap(label, width=max(3, int(radius * 22)), break_long_words=True)
    wrapped_label = (
        "\n".join(fallback_lines[: max(1, int(radius * 10))]) if fallback_lines else label
    )
    return wrapped_label, 5


def render_keyword_bubble_chart(conn: connection, podcast_id: int) -> None:
    """Render a packed circle bubble chart of keywords for a podcast.

    Each bubble represents a keyword, sized proportionally to how often it
    appears across episodes of the podcast.

    Args:
        conn: An open psycopg2 database connection.
        podcast_id: The ID of the podcast to generate the chart for.

    Example:
        >>> render_keyword_bubble_chart(conn, podcast_id=1)
    """
    keywords_data = get_keywords_for_podcast(conn, podcast_id)

    if not keywords_data:
        st.info("No keywords available for this podcast yet.")
        return

    keywords_data = sorted(keywords_data, key=lambda x: x[1], reverse=True)[:20]
    labels = [kw for kw, _ in keywords_data]
    counts = [count for _, count in keywords_data]

    circles = circlify.circlify(
        counts,
        show_enclosure=False,
        target_enclosure=circlify.Circle(x=0, y=0, r=1),
    )
    circles = list(reversed(circles))

    n = len(circles)
    palette = [_BUBBLE_PALETTE[i % len(_BUBBLE_PALETTE)] for i in range(n)]

    # --- CONFIGURING DIMENSIONS HERE ---
    # Width = 7 inches, Height = 5 inches
    fig, ax = plt.subplots(figsize=(3.5, 2.5))

    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_BG_COLOR)
    ax.set_aspect("equal")
    ax.axis("off")

    for i, (circle, label) in enumerate(zip(circles, labels, strict=True)):
        x, y, r = circle.x, circle.y, circle.r
        patch = plt.Circle((x, y), r, color=palette[i], alpha=0.90)
        ax.add_patch(patch)

        wrapped_label, fontsize = _fit_bubble_label(label, r)
        text = ax.text(
            x,
            y,
            wrapped_label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontfamily=_DASHBOARD_FONT_FAMILY,
            fontweight="normal",
            color="white",
            linespacing=0.95,
            clip_on=True,
        )
        text.set_clip_path(patch)

    ax.autoscale_view()
    plt.tight_layout(pad=0)

    st.pyplot(fig, use_container_width=True)


def render_sentiment_line_chart(conn: connection, podcast_id: int) -> None:
    """Render an Altair line graph of sentiment score over time for a podcast.

    Each point represents an episode plotted by its publication date and
    sentiment score. The line connects episodes in chronological order.

    Args:
        conn: An open psycopg2 database connection.
        podcast_id: The ID of the podcast to generate the chart for.

    Example:
        >>> render_sentiment_line_chart(conn, podcast_id=1)
    """
    data = get_sentiment_over_time(conn, podcast_id)

    if not data:
        st.info("No sentiment data available for this podcast yet.")
        return

    df = pd.DataFrame(data)
    df["pub_date"] = pd.to_datetime(df["pub_date"])

    line = (
        alt.Chart(df)
        .mark_line(color="#cb785c", strokeWidth=2)
        .encode(
            x=alt.X("pub_date:T", title="Publication Date", axis=alt.Axis(format="%b %Y")),
            y=alt.Y(
                "sentiment_score:Q",
                title="Sentiment Score",
                scale=alt.Scale(domain=[-1, 1]),
            ),
            tooltip=[
                alt.Tooltip("pub_date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("sentiment_score:Q", title="Sentiment", format=".2f"),
            ],
        )
    )

    points = (
        alt.Chart(df)
        .mark_point(color="#cb785c", filled=True, size=60)
        .encode(
            x=alt.X("pub_date:T"),
            y=alt.Y("sentiment_score:Q"),
            tooltip=[
                alt.Tooltip("pub_date:T", title="Date", format="%d %b %Y"),
                alt.Tooltip("sentiment_score:Q", title="Sentiment", format=".2f"),
            ],
        )
    )

    zero_line = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(color="#d3d2ca", strokeDash=[4, 4], strokeWidth=1)
        .encode(y=alt.Y("y:Q"))
    )

    chart = (
        (zero_line + line + points)
        .properties(height=300)
        .configure_axis(
            labelColor="#3d3a2a",
            titleColor="#3d3a2a",
            gridColor="#ecebe3",
        )
        .configure_view(strokeWidth=0, fill="transparent")
    )

    st.altair_chart(chart, use_container_width=True)
