import html
from unittest.mock import patch

import pytest
from app import get_sentiment_badge, render_episode_card

# ---------------------------------------------------------------------------
# get_sentiment_badge
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "score, expected_label, expected_emoji",
    [
        (1.0, "Positive", "↗"),
        (0.51, "Positive", "↗"),
        (0.5, "Neutral", "→"),
        (0.0, "Neutral", "→"),
        (-0.5, "Neutral", "→"),
        (-0.51, "Negative", "↘"),
        (-1.0, "Negative", "↘"),
    ],
)
def test_get_sentiment_badge_returns_correct_label(
    score: float, expected_label: str, expected_emoji: str
) -> None:
    result = get_sentiment_badge(score)

    assert expected_label in result
    assert expected_emoji in result


def test_get_sentiment_badge_returns_html_span() -> None:
    result = get_sentiment_badge(0.0)

    assert result.startswith("<span")
    assert result.endswith("</span>")


# ---------------------------------------------------------------------------
# render_episode_card
# ---------------------------------------------------------------------------


@pytest.fixture
def full_episode() -> dict:
    return {
        "episode_title": "Test Episode",
        "podcast_title": "Test Podcast",
        "sentiment_score": 0.8,
        "summary": "A great episode.",
        "time_since_published": "3 hours ago",
    }


def test_render_episode_card_with_full_episode_renders_badge_and_summary(
    full_episode: dict,
) -> None:
    with patch("app.st") as mock_st:
        render_episode_card(full_episode)

    mock_st.markdown.assert_called_once()
    rendered_html = mock_st.markdown.call_args[0][0]
    assert "Positive" in rendered_html
    assert html.escape("A great episode.") in rendered_html


def test_render_episode_card_with_no_score_omits_badge(full_episode: dict) -> None:
    full_episode["sentiment_score"] = None

    with patch("app.st") as mock_st:
        render_episode_card(full_episode)

    rendered_html = mock_st.markdown.call_args[0][0]
    assert "Positive" not in rendered_html
    assert "Negative" not in rendered_html
    assert "Neutral" not in rendered_html


def test_render_episode_card_with_no_summary_omits_summary_div(
    full_episode: dict,
) -> None:
    full_episode["summary"] = None

    with patch("app.st") as mock_st:
        render_episode_card(full_episode)

    rendered_html = mock_st.markdown.call_args[0][0]
    assert "font-size:0.85rem" not in rendered_html


def test_render_episode_card_escapes_xss_in_title() -> None:
    episode = {
        "episode_title": "<script>alert('xss')</script>",
        "podcast_title": "Safe Podcast",
        "sentiment_score": None,
        "summary": None,
        "time_since_published": "1 hour ago",
    }

    with patch("app.st") as mock_st:
        render_episode_card(episode)

    rendered_html = mock_st.markdown.call_args[0][0]
    assert "<script>" not in rendered_html
    assert html.escape("<script>alert('xss')</script>") in rendered_html


def test_render_episode_card_missing_title_falls_back_to_default() -> None:
    episode = {
        "podcast_title": "Some Podcast",
        "sentiment_score": None,
        "summary": None,
        "time_since_published": "2 days ago",
    }

    with patch("app.st") as mock_st:
        render_episode_card(episode)

    rendered_html = mock_st.markdown.call_args[0][0]
    assert "Untitled Episode" in rendered_html
