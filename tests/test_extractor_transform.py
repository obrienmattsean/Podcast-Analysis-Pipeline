from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import transform  # noqa: E402
from pydantic import ValidationError


class TestGetAudioLinkFromEntry:
  def test_returns_audio_link_from_entry(self):
    entry = {
      "links": [
        {"type": "audio/mpeg", "href": "https://example.com/ep.mp3"},
      ]
    }
    result = transform.get_audio_link_from_entry(entry)
    assert result == "https://example.com/ep.mp3"

  def test_returns_first_audio_link_when_multiple(self):
    entry = {
      "links": [
        {"type": "text/html", "href": "https://example.com"},
        {"type": "audio/mpeg", "href": "https://example.com/ep1.mp3"},
        {"type": "audio/wav", "href": "https://example.com/ep2.wav"},
      ]
    }
    result = transform.get_audio_link_from_entry(entry)
    assert result == "https://example.com/ep1.mp3"

  def test_returns_none_when_no_audio_links(self):
    entry = {
      "links": [
        {"type": "text/html", "href": "https://example.com"},
      ]
    }
    result = transform.get_audio_link_from_entry(entry)
    assert result is None

  def test_returns_none_when_no_links(self):
    entry = {"title": "Episode"}
    result = transform.get_audio_link_from_entry(entry)
    assert result is None

  def test_raises_when_entry_not_dict(self):
    with pytest.raises(ValueError, match="Entry must be a dictionary"):
      transform.get_audio_link_from_entry([])


class TestParseEpisode:
  def test_returns_validated_episode(self, rss_episode_with_audio):
    episode = rss_episode_with_audio(2026, 5, 15, "Test Ep")
    result = transform.parse_episode(episode, podcast_id=1)

    assert result.podcast_id == 1
    assert result.title == "Test Ep"
    assert str(result.audio_link) == "https://example.com/ep.mp3"
    assert result.published_at == datetime(2026, 5, 15, 0, 0, 0)

  def test_raises_when_podcast_id_not_int(self, rss_episode_with_audio):
    episode = rss_episode_with_audio(2026, 5, 15)
    with pytest.raises(ValueError, match="podcast_id must be an integer"):
      transform.parse_episode(episode, podcast_id="bad")

  def test_raises_when_missing_published_date(self):
    episode = {
      "title": "No Date Episode",
      "links": [{"type": "audio/mpeg", "href": "https://example.com/ep.mp3"}],
    }
    with pytest.raises(ValueError, match="Episode missing published date"):
      transform.parse_episode(episode, podcast_id=1)

  def test_strips_title_whitespace(self, rss_episode_with_audio):
    episode = rss_episode_with_audio(2026, 5, 15, "  Padded Title  ")
    result = transform.parse_episode(episode, podcast_id=1)
    assert result.title == "Padded Title"

  def test_raises_when_invalid_audio_link(self, rss_episode):
    episode = rss_episode(2026, 5, 15, "Bad Audio")
    episode["links"] = [{"type": "audio/mpeg", "href": "https://example.com/ep.pdf"}]
    with pytest.raises(ValidationError):
      transform.parse_episode(episode, podcast_id=1)


class TestTransformEpisodesForPodcast:
  @patch("transform.parse_episode")
  def test_returns_transformed_episodes(self, mock_parse, validated_episode):
    mock_parse.return_value = validated_episode()
    podcast_data = {
      "podcast_id": 1,
      "podcast_title": "Test Pod",
      "new_episodes": [{"title": "ep1"}, {"title": "ep2"}],
    }

    result = transform.transform_episodes_for_podcast(podcast_data)

    assert len(result) == 2
    assert all(isinstance(ep, type(validated_episode())) for ep in result)
    assert mock_parse.call_count == 2

  @patch("transform.parse_episode")
  def test_skips_episodes_with_parsing_errors(self, mock_parse, validated_episode):
    mock_parse.side_effect = [
      validated_episode(),
      ValueError("Bad episode"),
      validated_episode(),
    ]
    podcast_data = {
      "podcast_id": 1,
      "podcast_title": "Test Pod",
      "new_episodes": [{"title": "ep1"}, {"title": "ep2"}, {"title": "ep3"}],
    }

    result = transform.transform_episodes_for_podcast(podcast_data)

    assert len(result) == 2

  @patch("transform.parse_episode")
  def test_returns_empty_when_all_fail(self, mock_parse):
    mock_parse.side_effect = ValueError("Bad")
    podcast_data = {
      "podcast_id": 1,
      "podcast_title": "Test Pod",
      "new_episodes": [{"title": "ep1"}],
    }

    result = transform.transform_episodes_for_podcast(podcast_data)

    assert len(result) == 0


class TestTransformAllPodcastEpisodes:
  @patch("transform.transform_episodes_for_podcast")
  def test_returns_transformed_data_for_all_podcasts(self, mock_transform):
    ep1 = MagicMock()
    ep2 = MagicMock()
    mock_transform.side_effect = [[ep1, ep2], [ep1]]

    podcast_entries = [
      {
        "podcast_id": 1,
        "podcast_title": "Pod A",
        "new_episodes": [{"title": "ep1"}, {"title": "ep2"}],
      },
      {
        "podcast_id": 2,
        "podcast_title": "Pod B",
        "new_episodes": [{"title": "ep3"}],
      },
    ]

    result = transform.transform_all_podcast_episodes(podcast_entries)

    assert len(result) == 2
    assert result[0]["podcast_id"] == 1
    assert result[0]["podcast_title"] == "Pod A"
    assert len(result[0]["new_episodes"]) == 2
    assert result[1]["podcast_id"] == 2
    assert len(result[1]["new_episodes"]) == 1

  @patch("transform.transform_episodes_for_podcast")
  def test_skips_podcasts_with_errors(self, mock_transform):
    ep1 = MagicMock()
    mock_transform.side_effect = [
      [ep1],
      RuntimeError("Transform error"),
      [ep1],
    ]

    podcast_entries = [
      {
        "podcast_id": 1,
        "podcast_title": "Pod A",
        "new_episodes": [{"title": "ep1"}],
      },
      {
        "podcast_id": 2,
        "podcast_title": "Pod B",
        "new_episodes": [{"title": "ep2"}],
      },
      {
        "podcast_id": 3,
        "podcast_title": "Pod C",
        "new_episodes": [{"title": "ep3"}],
      },
    ]

    result = transform.transform_all_podcast_episodes(podcast_entries)

    assert len(result) == 2
    assert result[0]["podcast_id"] == 1
    assert result[1]["podcast_id"] == 3
