"""Tests for cards.py card components."""

from unittest.mock import MagicMock, patch

import pytest
from cards import _build_badge_row, episode_card


@pytest.fixture
def base_episode() -> dict:
    return {
        "episode_title": "Test Episode",
        "podcast_title": "Test Podcast",
        "sentiment_score": 0.8,
        "brand_safety_score": 92,
        "summary": "A great episode.",
        "time_since_published": "3 hours ago",
        "keywords": [],
    }


# ---------------------------------------------------------------------------
# _build_badge_row
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score, expected_label, expected_color",
    [
        (0.8, "↗ Positive", "#28a745"),
        (0.0, "→ Neutral", "#6c757d"),
        (-0.8, "↘ Negative", "#dc3545"),
    ],
)
def test_build_badge_row_sentiment_label_and_color(
    score: float, expected_label: str, expected_color: str
) -> None:
    result = _build_badge_row(score, [])

    assert expected_label in result
    assert expected_color in result


def test_build_badge_row_no_score_omits_sentiment_span() -> None:
    result = _build_badge_row(None, [])

    assert result == ""


def test_build_badge_row_renders_keywords_as_inline_spans() -> None:
    result = _build_badge_row(None, ["AI", "Cloud"])

    assert result.count("<span") == 2


def test_build_badge_row_renders_all_passed_keywords() -> None:
    result = _build_badge_row(None, ["A", "B", "C", "D", "E"])

    assert result.count("<span") == 5


def test_build_badge_row_keywords_use_blue_color() -> None:
    result = _build_badge_row(None, ["Python"])

    assert "#0d6efd" in result


def test_build_badge_row_renders_sentiment_and_keywords_in_one_div() -> None:
    result = _build_badge_row(0.8, ["AI", "Cloud"])

    assert result.startswith("<div")
    assert result.count("<span") == 3


def test_build_badge_row_empty_score_and_no_keywords_returns_empty_string() -> None:
    assert _build_badge_row(None, []) == ""


# ---------------------------------------------------------------------------
# Brand safe badge
# ---------------------------------------------------------------------------


def test_episode_card_brand_safe_renders_green_html(base_episode: dict) -> None:
    base_episode["brand_safety_score"] = 92

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    right_col = mock_st.columns.return_value[1]
    markdown_calls = [str(c) for c in right_col.markdown.call_args_list]
    combined = " ".join(markdown_calls)
    assert "#dcfce7" in combined
    assert "#166534" in combined
    assert "Brand safe" in combined


def test_episode_card_not_brand_safe_renders_red_html(base_episode: dict) -> None:
    base_episode["brand_safety_score"] = 20

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    right_col = mock_st.columns.return_value[1]
    markdown_calls = [str(c) for c in right_col.markdown.call_args_list]
    combined = " ".join(markdown_calls)
    assert "#f8d7da" in combined
    assert "#842029" in combined
    assert "Unsafe" in combined


def test_episode_card_missing_brand_safety_score_omits_badge(base_episode: dict) -> None:
    del base_episode["brand_safety_score"]

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    right_col = mock_st.columns.return_value[1]
    markdown_calls = [str(c) for c in right_col.markdown.call_args_list]
    combined = " ".join(markdown_calls)
    assert "Brand safe" not in combined
    assert "Unsafe" not in combined


# ---------------------------------------------------------------------------
# Inline badge row in left column
# ---------------------------------------------------------------------------


def test_episode_card_no_score_and_no_keywords_skips_badge_row(base_episode: dict) -> None:
    base_episode["sentiment_score"] = None
    base_episode["keywords"] = []

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    left_col = mock_st.columns.return_value[0]
    left_col.__enter__.return_value.markdown.assert_not_called()


def test_episode_card_missing_keywords_renders_no_keyword_html(base_episode: dict) -> None:
    base_episode.pop("keywords", None)
    base_episode["sentiment_score"] = None

    with patch("cards.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        episode_card(base_episode)

    left_col = mock_st.columns.return_value[0]
    left_col.__enter__.return_value.markdown.assert_not_called()
