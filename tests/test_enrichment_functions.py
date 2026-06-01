"""Unit tests for the enrichment_functions module.

Tests cover LLM enrichment and S3 metadata/transcript retrieval with proper
error handling and validation of input parameters.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "enrich_upload"))

import json
from unittest.mock import MagicMock

import pytest
from enrichment_functions import (
    get_episode_metadata_from_s3,
    get_episode_transcript_from_s3,
    prompt_llm_for_enrichment,
)


class TestPromptLlmForEnrichment:
    """Tests for prompt_llm_for_enrichment function."""

    def test_prompt_llm_for_enrichment_success(self):
        """Test successful LLM enrichment with valid transcript."""
        mock_llm_client = MagicMock()
        enrichment_response = {
            "sentiment score": 3.5,
            "classification": "positive",
            "summary": "A great discussion about AI.",
            "hosts": ["John Doe"],
            "guests": ["Jane Smith"],
            "keywords": [["AI", "topic"], ["discussion", "concept"]],
        }
        mock_llm_client.chat.completions.create.return_value.choices[
            0
        ].message.content = json.dumps(enrichment_response)

        result = prompt_llm_for_enrichment(
            mock_llm_client, "This is a podcast transcript about AI."
        )

        assert result == enrichment_response
        assert result["sentiment score"] == 3.5
        assert result["classification"] == "positive"

    def test_prompt_llm_for_enrichment_empty_transcript(self):
        """Test LLM enrichment with empty transcript."""
        mock_llm_client = MagicMock()
        enrichment_response = {
            "sentiment score": 2.5,
            "classification": "neutral",
            "summary": "",
            "hosts": [],
            "guests": [],
            "keywords": [],
        }
        mock_llm_client.chat.completions.create.return_value.choices[
            0
        ].message.content = json.dumps(enrichment_response)

        result = prompt_llm_for_enrichment(mock_llm_client, "")

        assert result["summary"] == ""
        assert result["hosts"] == []
        assert result["guests"] == []

    def test_prompt_llm_for_enrichment_invalid_json_response(self):
        """Test that invalid JSON response raises exception."""
        mock_llm_client = MagicMock()
        mock_llm_client.chat.completions.create.return_value.choices[
            0
        ].message.content = "Invalid JSON"

        with pytest.raises(json.JSONDecodeError):
            prompt_llm_for_enrichment(mock_llm_client, "Valid transcript")

    def test_prompt_llm_for_enrichment_none_client(self):
        """Test that None LLM client raises AttributeError."""
        with pytest.raises(AttributeError):
            prompt_llm_for_enrichment(None, "Valid transcript")

    def test_prompt_llm_for_enrichment_none_transcript(self):
        """Test LLM enrichment with None transcript."""
        mock_llm_client = MagicMock()
        mock_llm_client.chat.completions.create.return_value.choices[
            0
        ].message.content = json.dumps(
            {
                "sentiment score": 2.5,
                "classification": "neutral",
                "summary": "",
                "hosts": [],
                "guests": [],
                "keywords": [],
            }
        )

        # Should work because None is converted to string in f-string
        result = prompt_llm_for_enrichment(mock_llm_client, None)
        assert isinstance(result, dict)


class TestGetEpisodeMetadataFromS3:
    """Tests for get_episode_metadata_from_s3 function."""

    def test_get_episode_metadata_from_s3_success(self):
        """Test successful metadata retrieval from S3."""
        mock_s3_client = MagicMock()
        metadata = {"episode_id": 1, "title": "Test Episode", "podcast_id": 1}
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=json.dumps(metadata).encode("utf-8")))
        }

        result = get_episode_metadata_from_s3(mock_s3_client, "s3://bucket/path/to/episode/")

        assert result == metadata
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="bucket", Key="path/to/episode/metadata.json"
        )

    def test_get_episode_metadata_from_s3_invalid_path_type(self):
        """Test that non-string path raises TypeError."""
        mock_s3_client = MagicMock()

        with pytest.raises(TypeError, match="S3 path must be a string"):
            get_episode_metadata_from_s3(mock_s3_client, 12345)

    def test_get_episode_metadata_from_s3_invalid_path_format(self):
        """Test that path not starting with 's3://' raises ValueError."""
        mock_s3_client = MagicMock()

        with pytest.raises(ValueError, match="must start with 's3://'"):
            get_episode_metadata_from_s3(mock_s3_client, "http://bucket/path/")

    def test_get_episode_metadata_from_s3_empty_path(self):
        """Test that empty path raises ValueError."""
        mock_s3_client = MagicMock()

        with pytest.raises(ValueError, match="must start with 's3://'"):
            get_episode_metadata_from_s3(mock_s3_client, "")

    def test_get_episode_metadata_from_s3_s3_error(self):
        """Test that S3 error is caught and re-raised."""
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.side_effect = Exception("NoSuchKey")

        with pytest.raises(Exception, match="NoSuchKey"):
            get_episode_metadata_from_s3(mock_s3_client, "s3://bucket/path/")


class TestGetEpisodeTranscriptFromS3:
    """Tests for get_episode_transcript_from_s3 function."""

    def test_get_episode_transcript_from_s3_success(self):
        """Test successful transcript retrieval from S3."""
        mock_s3_client = MagicMock()
        transcript = "This is a podcast transcript about machine learning."
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=transcript.encode("utf-8")))
        }

        result = get_episode_transcript_from_s3(mock_s3_client, "s3://bucket/21/92/")

        assert result == transcript
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="bucket", Key="21/92/transcript.txt"
        )

    def test_get_episode_transcript_from_s3_invalid_path_type(self):
        """Test that non-string path raises TypeError."""
        mock_s3_client = MagicMock()

        with pytest.raises(TypeError, match="S3 path must be a string"):
            get_episode_transcript_from_s3(mock_s3_client, ["s3://bucket/"])

    def test_get_episode_transcript_from_s3_invalid_path_format(self):
        """Test that path not starting with 's3://' raises ValueError."""
        mock_s3_client = MagicMock()

        with pytest.raises(ValueError, match="must start with 's3://'"):
            get_episode_transcript_from_s3(mock_s3_client, "file:///local/path/")

    def test_get_episode_transcript_from_s3_empty_transcript(self):
        """Test transcript retrieval with empty file."""
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=MagicMock(return_value=b""))
        }

        result = get_episode_transcript_from_s3(mock_s3_client, "s3://bucket/path/")

        assert result == ""

    def test_get_episode_transcript_from_s3_s3_error(self):
        """Test that S3 error is caught and re-raised."""
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.side_effect = Exception("Access Denied")

        with pytest.raises(Exception, match="Access Denied"):
            get_episode_transcript_from_s3(mock_s3_client, "s3://bucket/path/")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
