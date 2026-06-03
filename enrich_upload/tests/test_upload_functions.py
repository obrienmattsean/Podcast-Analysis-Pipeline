"""Unit tests for the upload_functions module.

Tests cover data combination and RDS upload operations with proper error
handling and validation of input parameters.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from upload_functions import combine_enrichments, upload_to_rds


class TestCombineEnrichments:
    """Tests for combine_enrichments function."""

    def test_combine_enrichments_success(self):
        """Test successful combination of enrichments with moderation."""
        episode_metadata = {
            "episode_id": 1,
            "podcast_id": 1,
            "title": "Test Episode",
            "audio_link": "http://example.com/audio.mp3",
            "published_at": "2024-01-15T10:00:00",
        }
        enrichments = {
            "sentiment score": 3.5,
            "classification": "positive",
            "summary": "A great episode.",
            "hosts": ["Host 1"],
            "guests": ["Guest 1"],
            "keywords": [["topic1", "category1"], ["topic2", "category2"]],
        }
        moderation = {
            "harassment": False,
            "hate": False,
            "violence": False,
            "sexual": False,
        }

        result = combine_enrichments(episode_metadata, enrichments, moderation)

        assert result["episode"]["episode_id"] == 1
        assert result["episode"]["sentiment_score"] == 3.5
        assert result["episode"]["summary"] == "A great episode."
        assert "Host 1" in result["entities"]
        assert "Guest 1" in result["entities"]
        assert result["episode"]["harassment"] is False
        assert result["episode"]["hate"] is False

    def test_combine_enrichments_with_flagged_moderation(self):
        """Test combination where moderation flags content."""
        episode_metadata = {
            "episode_id": 1,
            "podcast_id": 1,
            "title": "Test Episode",
            "audio_link": "http://example.com/audio.mp3",
            "published_at": "2024-01-15",
        }
        enrichments = {
            "sentiment score": 2.5,
            "classification": "neutral",
            "summary": "Neutral episode.",
            "hosts": [],
            "guests": [],
            "keywords": [],
        }
        moderation = {
            "harassment": False,
            "harassment_threatening": False,
            "hate": True,
            "hate_threatening": False,
            "illicit": False,
            "illicit_violent": False,
            "self_harm": False,
            "self_harm_instructions": False,
            "self_harm_intent": False,
            "sexual": False,
            "sexual_minors": False,
            "violence": False,
            "violence_graphic": False,
        }

        result = combine_enrichments(episode_metadata, enrichments, moderation)

        assert result["episode"]["hate"] is True
        assert result["episode"]["flagged"] is True

    def test_combine_enrichments_no_hosts_or_guests(self):
        """Test combination with no hosts or guests."""
        episode_metadata = {
            "episode_id": 1,
            "podcast_id": 1,
            "title": "Test Episode",
            "audio_link": "http://example.com/audio.mp3",
            "published_at": "2024-01-15",
        }
        enrichments = {
            "sentiment score": 2.5,
            "classification": "neutral",
            "summary": "Neutral episode.",
            "hosts": [],
            "guests": [],
            "keywords": [],
        }
        moderation = {
            "harassment": False,
            "hate": False,
            "violence": False,
        }

        result = combine_enrichments(episode_metadata, enrichments, moderation)

        assert result["entities"] == {}

    def test_combine_enrichments_missing_metadata_keys(self):
        """Test combination with missing metadata keys."""
        episode_metadata = {"episode_id": 1}
        enrichments = {
            "sentiment score": 3.0,
            "classification": "positive",
            "summary": "Test",
            "hosts": [],
            "guests": [],
            "keywords": [],
        }
        moderation = {
            "harassment": False,
            "hate": False,
        }

        result = combine_enrichments(episode_metadata, enrichments, moderation)

        assert result["episode"]["episode_id"] == 1
        assert result["episode"]["podcast_id"] is None
        assert result["episode"]["title"] is None

    def test_combine_enrichments_none_embedding(self):
        """Test combination with None embedding."""
        episode_metadata = {
            "episode_id": 1,
            "podcast_id": 1,
            "title": "Test",
            "audio_link": "http://example.com/audio.mp3",
            "published_at": "2024-01-15",
        }
        enrichments = {
            "sentiment score": 3.0,
            "classification": "positive",
            "summary": "Test",
            "hosts": [],
            "guests": [],
            "keywords": [],
        }
        moderation = {
            "harassment": False,
            "violence": False,
        }

        result = combine_enrichments(episode_metadata, enrichments, moderation)

        assert "episode" in result
        assert result["episode"]["sentiment_score"] == 3.0

    def test_combine_enrichments_invalid_published_date(self):
        """Test combination with None published date."""
        episode_metadata = {
            "episode_id": 1,
            "podcast_id": 1,
            "title": "Test",
            "audio_link": "http://example.com/audio.mp3",
            "published_at": None,
        }
        enrichments = {
            "sentiment score": 3.0,
            "classification": "positive",
            "summary": "Test",
            "hosts": [],
            "guests": [],
            "keywords": [],
        }
        moderation = {
            "harassment": False,
            "sexual": False,
        }

        result = combine_enrichments(episode_metadata, enrichments, moderation)
        assert result["episode"]["pub_date"] is None


class TestUploadToRds:
    """Tests for upload_to_rds function."""

    def test_upload_to_rds_success(self):
        """Test successful upload to RDS."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        enrichment_dict = {
            "episode": {
                "episode_id": 1,
                "podcast_id": 1,
                "title": "Test",
                "audio_url": "http://example.com/audio.mp3",
                "pub_date": "2024-01-15",
                "duration_seconds": None,
                "sentiment_score": 3.5,
                "created_at": datetime.now(),
                "summary": "Test summary",
                "harassment": False,
                "harassment_threatening": False,
                "hate": False,
                "hate_threatening": False,
                "illicit": False,
                "illicit_violent": False,
                "self_harm": False,
                "self_harm_instructions": False,
                "self_harm_intent": False,
                "sexual": False,
                "sexual_minors": False,
                "violence": False,
                "violence_graphic": False,
                "flagged": False,
            },
            "entities": {
                "host1": {"name": "Host 1", "entity_type": "host"},
                "guest1": {"name": "Guest 1", "entity_type": "guest"},
            },
        }

        upload_to_rds(enrichment_dict, mock_connection)

        # Verify cursor was created and operations were called
        mock_connection.cursor.assert_called_once()
        assert mock_cursor.execute.call_count >= 3  # At least one UPDATE + two INSERTs
        mock_connection.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_upload_to_rds_empty_entities(self):
        """Test upload with no entities."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor

        enrichment_dict = {
            "episode": {
                "episode_id": 1,
                "podcast_id": 1,
                "title": "Test",
                "audio_url": "http://example.com/audio.mp3",
                "pub_date": "2024-01-15",
                "duration_seconds": None,
                "sentiment_score": 3.5,
                "created_at": datetime.now(),
                "summary": "Test summary",
                "harassment": False,
                "harassment_threatening": False,
                "hate": False,
                "hate_threatening": False,
                "illicit": False,
                "illicit_violent": False,
                "self_harm": False,
                "self_harm_instructions": False,
                "self_harm_intent": False,
                "sexual": False,
                "sexual_minors": False,
                "violence": False,
                "violence_graphic": False,
                "flagged": False,
            },
            "entities": {},
        }

        upload_to_rds(enrichment_dict, mock_connection)

        # Should still succeed with empty entities
        mock_connection.commit.assert_called_once()

    def test_upload_to_rds_database_error(self):
        """Test that database error is caught and rolled back."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        enrichment_dict = {
            "episode": {
                "episode_id": 1,
                "podcast_id": 1,
                "title": "Test",
                "audio_url": "http://example.com/audio.mp3",
                "pub_date": "2024-01-15",
                "duration_seconds": None,
                "sentiment_score": 3.5,
                "created_at": datetime.now(),
                "summary": "Test summary",
                "harassment": False,
                "harassment_threatening": False,
                "hate": False,
                "hate_threatening": False,
                "illicit": False,
                "illicit_violent": False,
                "self_harm": False,
                "self_harm_instructions": False,
                "self_harm_intent": False,
                "sexual": False,
                "sexual_minors": False,
                "violence": False,
                "violence_graphic": False,
                "flagged": False,
            },
            "entities": {},
        }

        with pytest.raises(Exception, match=r"Database error"):
            upload_to_rds(enrichment_dict, mock_connection)

        mock_connection.rollback.assert_called_once()

    def test_upload_to_rds_none_connection(self):
        """Test that None connection raises AttributeError."""
        enrichment_dict = {
            "episode": {
                "episode_id": 1,
                "podcast_id": 1,
                "title": "Test",
                "audio_url": "http://example.com/audio.mp3",
                "pub_date": "2024-01-15",
                "duration_seconds": None,
                "sentiment_score": 3.5,
                "created_at": datetime.now(),
                "summary": "Test summary",
            },
            "entities": {},
        }

        with pytest.raises(AttributeError):
            upload_to_rds(enrichment_dict, None)

    def test_upload_to_rds_missing_episode_data(self):
        """Test upload with missing required episode data."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = KeyError("episode_id")

        enrichment_dict = {
            "episode": {
                "podcast_id": 1,
                "title": "Test",
                # Missing episode_id
            },
            "entities": {},
        }

        with pytest.raises(KeyError):
            upload_to_rds(enrichment_dict, mock_connection)

        mock_connection.rollback.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
