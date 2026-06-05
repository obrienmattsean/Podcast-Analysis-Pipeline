"""Tests for visualisation.py chart components."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from visualisation import _fit_bubble_label, render_sentiment_line_chart


@pytest.fixture
def mock_conn() -> MagicMock:
    return MagicMock()


# ---------------------------------------------------------------------------
# render_sentiment_line_chart
# ---------------------------------------------------------------------------


def test_render_sentiment_line_chart_with_no_data_shows_info_message(
    mock_conn: MagicMock,
) -> None:
    with (
        patch("visualisation.get_sentiment_over_time", return_value=[]),
        patch("visualisation.st") as mock_st,
    ):
        render_sentiment_line_chart(mock_conn, podcast_id=1)

    mock_st.info.assert_called_once()


def test_render_sentiment_line_chart_with_data_calls_altair_chart(
    mock_conn: MagicMock,
) -> None:
    sentiment_data = [
        {"pub_date": datetime(2024, 1, 1), "sentiment_score": 0.3},
        {"pub_date": datetime(2024, 2, 1), "sentiment_score": -0.1},
        {"pub_date": datetime(2024, 3, 1), "sentiment_score": 0.7},
    ]
    with (
        patch("visualisation.get_sentiment_over_time", return_value=sentiment_data),
        patch("visualisation.st") as mock_st,
    ):
        render_sentiment_line_chart(mock_conn, podcast_id=2)

    mock_st.altair_chart.assert_called_once()


def test_render_sentiment_line_chart_passes_podcast_id_to_db(
    mock_conn: MagicMock,
) -> None:
    with (
        patch("visualisation.get_sentiment_over_time", return_value=[]) as mock_db,
        patch("visualisation.st"),
    ):
        render_sentiment_line_chart(mock_conn, podcast_id=99)

    mock_db.assert_called_once_with(mock_conn, 99)


def test_render_sentiment_line_chart_with_single_point_renders_chart(
    mock_conn: MagicMock,
) -> None:
    sentiment_data = [{"pub_date": datetime(2024, 6, 1), "sentiment_score": 0.5}]
    with (
        patch("visualisation.get_sentiment_over_time", return_value=sentiment_data),
        patch("visualisation.st") as mock_st,
    ):
        render_sentiment_line_chart(mock_conn, podcast_id=3)

    mock_st.altair_chart.assert_called_once()


# ---------------------------------------------------------------------------
# _fit_bubble_label
# ---------------------------------------------------------------------------


def test_fit_bubble_label_wraps_long_text_for_small_bubble() -> None:
    wrapped, font_size = _fit_bubble_label("this is a very long keyword phrase", radius=0.2)

    assert "\n" in wrapped
    assert 5 <= font_size <= 12


def test_fit_bubble_label_avoids_ellipsis_cutoff_for_small_bubble() -> None:
    wrapped, _ = _fit_bubble_label("one two three four five six seven eight nine ten", radius=0.12)

    assert "..." not in wrapped


def test_fit_bubble_label_increases_font_for_larger_bubbles() -> None:
    _, small_font = _fit_bubble_label("keyword", radius=0.12)
    _, large_font = _fit_bubble_label("keyword", radius=0.35)

    assert large_font > small_font
