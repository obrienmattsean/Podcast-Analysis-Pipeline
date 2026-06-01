from unittest.mock import MagicMock, patch

import pytest
from s3_utils import EpisodeS3


class TestEpisodeS3:
    def test_episode_s3_properties(self, mock_episode_s3_uri):
        uri = mock_episode_s3_uri
        episode_s3 = EpisodeS3(uri=uri)

        assert episode_s3.bucket == "test-bucket"
        assert episode_s3.podcast_id == "07"
        assert episode_s3.episode_id == "88"
        assert episode_s3.metadata_key == "07/88/metadata.json"

    def test_episode_s3_transcript_key(self, mock_episode_s3_uri):
        uri = mock_episode_s3_uri
        episode_s3 = EpisodeS3(uri=uri)

        assert episode_s3.transcript_key == "07/88/transcript.txt"

    def test_get_audio_link_valid(self, mock_episode_s3_uri):
        episode = EpisodeS3(uri=mock_episode_s3_uri)
        mock_s3 = MagicMock()

        with patch.object(
            episode, "read_metadata", return_value={"audio_link": "https://example.com/audio.mp3"}
        ):
            audio_link = episode.get_audio_link(mock_s3)

        assert audio_link == "https://example.com/audio.mp3"

    def test_get_audio_link_missing(self, mock_episode_s3_uri):
        episode = EpisodeS3(uri=mock_episode_s3_uri)
        mock_s3 = MagicMock()

        with patch.object(episode, "read_metadata", return_value={}):
            with pytest.raises(ValueError, match="metadata.json is missing a valid audio_link"):
                episode.get_audio_link(mock_s3)

    def test_get_audio_link_invalid_type(self, mock_episode_s3_uri):
        episode = EpisodeS3(uri=mock_episode_s3_uri)
        mock_s3 = MagicMock()

        with patch.object(episode, "read_metadata", return_value={"audio_link": 123}):
            with pytest.raises(ValueError, match="metadata.json is missing a valid audio_link"):
                episode.get_audio_link(mock_s3)

    def test_upload_transcript_calls_put_object_with_correct_args(self, mock_episode_s3_uri):
        episode = EpisodeS3(uri=mock_episode_s3_uri)
        mock_s3 = MagicMock()
        transcript = "This is the transcript text."

        episode.upload_transcript(mock_s3, transcript)

        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="07/88/transcript.txt",
            Body=transcript,
            ContentType="text/plain",
        )

    def test_upload_transcript_returns_correct_s3_uri(self, mock_episode_s3_uri):
        episode = EpisodeS3(uri=mock_episode_s3_uri)
        mock_s3 = MagicMock()

        result = episode.upload_transcript(mock_s3, "Some transcript.")

        assert result == "s3://test-bucket/07/88/transcript.txt"

    def test_get_audio_link_invalid(self, mock_episode_s3_uri):
        episode = EpisodeS3(uri=mock_episode_s3_uri)
        mock_s3 = MagicMock()

        with patch.object(episode, "read_metadata", return_value={"audio_link": 123}):
            with pytest.raises(ValueError, match="metadata.json is missing a valid audio_link"):
                episode.get_audio_link(mock_s3)
