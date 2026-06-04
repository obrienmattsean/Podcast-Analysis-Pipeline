"""Visualization components for podcast analysis dashboard."""

import circlify
import matplotlib.pyplot as plt
import streamlit as st
from db_functions import get_keywords_for_podcast
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
    fig, ax = plt.subplots(figsize=(7, 5))

    fig.patch.set_facecolor(_BG_COLOR)
    ax.set_facecolor(_BG_COLOR)
    ax.set_aspect("equal")
    ax.axis("off")

    for i, (circle, label) in enumerate(zip(circles, labels, strict=True)):
        x, y, r = circle.x, circle.y, circle.r
        patch = plt.Circle((x, y), r, color=palette[i], alpha=0.90)
        ax.add_patch(patch)

        fontsize = max(6, min(15, int(r * 38)))
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=fontsize,
            fontweight="bold",
            color="white",
        )

    ax.autoscale_view()
    plt.tight_layout(pad=0)

    st.pyplot(fig, use_container_width=True)
