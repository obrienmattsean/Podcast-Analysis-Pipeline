"""Unit tests for transform module (RSS entry validation and model conversion)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import transform  # noqa: E402
from pydantic import ValidationError


class TestGetAudioLinkFromEntry:
    """Tests for get_audio_link_from_entry function."""

    def test_get_audio_link_extracts_first_audio_link(self):
        """Verify get_audio_link_from_entry extracts first audio link from entry."""
        entry = {
            "links": [
                {"type": "audio/mpeg", "href": "https://example.com/ep.mp3"},
            ]
        }

        result = transform.get_audio_link_from_entry(entry)

        assert result == "https://example.com/ep.mp3"

    def test_get_audio_link_returns_first_when_multiple_present(self):
        """Verify get_audio_link_from_entry returns first audio link when multiple exist."""
        entry = {
            "links": [
                {"type": "text/html", "href": "https://example.com"},
                {"type": "audio/mpeg", "href": "https://example.com/ep1.mp3"},
                {"type": "audio/wav", "href": "https://example.com/ep2.wav"},
            ]
        }

        result = transform.get_audio_link_from_entry(entry)

        assert result == "https://example.com/ep1.mp3"

    def test_get_audio_link_raises_when_no_audio_links_found(self):
        """Verify get_audio_link_from_entry raises ValueError when no audio links exist."""
        entry = {
            "links": [
                {"type": "text/html", "href": "https://example.com"},
            ]
        }

        with pytest.raises(ValueError, match="No audio link found in entry"):
            transform.get_audio_link_from_entry(entry)

    def test_get_audio_link_raises_when_no_links_present(self):
        """Verify get_audio_link_from_entry raises ValueError when entry has no links."""
        entry = {"title": "Episode"}

        with pytest.raises(ValueError, match="No audio link found in entry"):
            transform.get_audio_link_from_entry(entry)

    def test_get_audio_link_raises_when_entry_not_dict(self):
        """Verify get_audio_link_from_entry raises ValueError when entry is not a dict."""
        with pytest.raises(ValueError, match="Entry must be a dictionary"):
            transform.get_audio_link_from_entry([])  # type: ignore[invalid-argument-type]


class TestParseEpisode:
    """Tests for parse_episode function."""

    def test_parse_episode_returns_validated_episode_model(self, rss_episode_with_audio):
        """Verify parse_episode converts RSS entry to ValidatedEpisode model."""
        episode = rss_episode_with_audio(2026, 5, 15, "Test Ep")

        result = transform.parse_episode(episode, podcast_id=1)

        assert result.podcast_id == 1
        assert result.title == "Test Ep"
        assert str(result.audio_link) == "https://example.com/ep.mp3"
        assert result.published_at == datetime(2026, 5, 15, 0, 0, 0)

    def test_parse_episode_raises_when_podcast_id_not_int(self, rss_episode_with_audio):
        """Verify parse_episode raises ValueError when podcast_id is not an integer."""
        episode = rss_episode_with_audio(2026, 5, 15)

        with pytest.raises(ValueError, match="podcast_id must be an integer"):
            transform.parse_episode(episode, podcast_id="bad")  # type: ignore[invalid-argument-type]

    def test_parse_episode_raises_when_published_date_missing(self):
        """Verify parse_episode raises ValueError when published_parsed is missing."""
        episode = {
            "title": "No Date Episode",
            "links": [{"type": "audio/mpeg", "href": "https://example.com/ep.mp3"}],
        }

        with pytest.raises(ValueError, match="Episode missing published date"):
            transform.parse_episode(episode, podcast_id=1)

    def test_parse_episode_strips_title_whitespace(self, rss_episode_with_audio):
        """Verify parse_episode strips leading/trailing whitespace from title."""
        episode = rss_episode_with_audio(2026, 5, 15, "  Padded Title  ")

        result = transform.parse_episode(episode, podcast_id=1)

        assert result.title == "Padded Title"

    def test_parse_episode_raises_when_audio_link_invalid_extension(self, rss_episode):
        """Verify parse_episode raises ValidationError when audio URL has invalid extension."""
        episode = rss_episode(2026, 5, 15, "Bad Audio")
        episode["links"] = [{"type": "audio/mpeg", "href": "https://example.com/ep.pdf"}]

        with pytest.raises(ValidationError):
            transform.parse_episode(episode, podcast_id=1)


class TestTransformEpisodesForPodcast:
    """Tests for transform_episodes_for_podcast function."""

    @patch("transform.parse_episode")
    def test_transform_returns_validated_episodes(self, mock_parse, validated_episode):
        """Verify transform_episodes_for_podcast returns list of validated episodes."""
        mock_parse.return_value = validated_episode()
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Test Pod",
            "new_episodes": [{"title": "ep1"}, {"title": "ep2"}],
        }

        result = transform.transform_episodes_for_podcast(podcast_data)

        assert len(result) == 2
        assert mock_parse.call_count == 2

    @patch("transform.parse_episode")
    def test_transform_skips_episodes_with_parse_errors(self, mock_parse, validated_episode):
        """Verify transform_episodes_for_podcast skips episodes that fail validation."""
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
    def test_transform_returns_empty_when_all_fail(self, mock_parse):
        """Verify transform_episodes_for_podcast returns empty list when all episodes fail."""
        mock_parse.side_effect = ValueError("Bad")
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Test Pod",
            "new_episodes": [{"title": "ep1"}],
        }

        result = transform.transform_episodes_for_podcast(podcast_data)

        assert len(result) == 0


class TestTransformAllPodcastEpisodes:
    """Tests for transform_all_podcast_episodes orchestration function."""

    @patch("transform.transform_episodes_for_podcast")
    def test_transform_all_returns_data_for_all_podcasts(self, mock_transform):
        """Verify transform_all_podcast_episodes transforms all podcasts."""
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
        assert mock_transform.call_count == 2
        assert result[0]["podcast_id"] == 1
        assert result[0]["podcast_title"] == "Pod A"
        assert len(result[0]["new_episodes"]) == 2
        assert result[1]["podcast_id"] == 2
        assert len(result[1]["new_episodes"]) == 1

    @patch("transform.transform_episodes_for_podcast")
    def test_transform_all_continues_after_podcast_error(self, mock_transform):
        """Verify transform_all_podcast_episodes continues after podcast transform errors."""
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
