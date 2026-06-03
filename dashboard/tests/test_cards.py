"""Tests for cards.py card components."""

from unittest.mock import MagicMock, call, patch

import pytest
from cards import episode_card


@pytest.fixture
def base_episode() -> dict:
    return {
        "episode_title": "Test Episode",
        "podcast_title": "Test Podcast",
        "sentiment_score": 0.8,
        "summary": "A great episode.",
        "time_since_published": "3 hours ago",
        "flagged": False,
    }


def _right_markdown_calls(mock_st: MagicMock) -> list[str]:
    """Return all HTML strings passed to markdown on the right column context manager."""
    right_col = mock_st.columns.return_value[1]
    return [c[0][0] for c in right_col.__enter__.return_value.markdown.call_args_list]


# ---------------------------------------------------------------------------
# Brand safe badge
# ---------------------------------------------------------------------------


def test_episode_card_brand_safe_renders_green_html(base_episode: dict) -> None:
    base_episode["flagged"] = False

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    right_col = mock_st.columns.return_value[1]
    markdown_calls = [str(c) for c in right_col.__enter__.return_value.markdown.call_args_list]
    combined = " ".join(markdown_calls)
    assert "#28a745" in combined
    assert "Brand Safe" in combined


def test_episode_card_not_brand_safe_renders_red_html(base_episode: dict) -> None:
    base_episode["flagged"] = True

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    right_col = mock_st.columns.return_value[1]
    markdown_calls = [str(c) for c in right_col.__enter__.return_value.markdown.call_args_list]
    combined = " ".join(markdown_calls)
    assert "#dc3545" in combined
    assert "Not Brand Safe" in combined


def test_episode_card_missing_flagged_defaults_to_brand_safe(base_episode: dict) -> None:
    del base_episode["flagged"]

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    right_col = mock_st.columns.return_value[1]
    markdown_calls = [str(c) for c in right_col.__enter__.return_value.markdown.call_args_list]
    combined = " ".join(markdown_calls)
    assert "#28a745" in combined
    assert "Brand Safe" in combined


# ---------------------------------------------------------------------------
# Sentiment badge in left column
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score, expected_label",
    [
        (0.8, "↗ Positive"),
        (0.0, "→ Neutral"),
        (-0.8, "↘ Negative"),
    ],
)
def test_episode_card_sentiment_badge_shown_in_left_column(
    base_episode: dict, score: float, expected_label: str
) -> None:
    base_episode["sentiment_score"] = score

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    left_col = mock_st.columns.return_value[0]
    left_col.__enter__.return_value.badge.assert_called_once()
    call_label = left_col.__enter__.return_value.badge.call_args[0][0]
    assert call_label == expected_label


def test_episode_card_no_score_omits_sentiment_badge(base_episode: dict) -> None:
    base_episode["sentiment_score"] = None

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    left_col = mock_st.columns.return_value[0]
    left_col.__enter__.return_value.badge.assert_not_called()
