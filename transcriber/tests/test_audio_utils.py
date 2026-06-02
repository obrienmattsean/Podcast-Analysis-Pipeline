from unittest.mock import patch

from audio_utils import download_audio_file


class TestDownloadAudioFile:
    def test_download_audio_file_writes_response_bytes_to_path(
        self, tmp_path, mock_urlopen_response
    ):
        output_path = tmp_path / "episode.mp3"
        mock_urlopen_response.read.return_value = b"fake audio bytes"

        with patch("audio_utils.urlopen", return_value=mock_urlopen_response):
            download_audio_file("https://example.com/episode.mp3", output_path)

        assert output_path.read_bytes() == b"fake audio bytes"

    def test_download_audio_file_returns_output_path(self, tmp_path, mock_urlopen_response):
        output_path = tmp_path / "episode.mp3"

        with patch("audio_utils.urlopen", return_value=mock_urlopen_response):
            result = download_audio_file("https://example.com/episode.mp3", output_path)

        assert result == output_path

    def test_download_audio_file_creates_parent_directories(self, tmp_path, mock_urlopen_response):
        output_path = tmp_path / "nested" / "dir" / "episode.mp3"

        with patch("audio_utils.urlopen", return_value=mock_urlopen_response):
            download_audio_file("https://example.com/episode.mp3", output_path)

        assert output_path.parent.exists()

    def test_download_audio_file_passes_timeout_to_urlopen(self, tmp_path, mock_urlopen_response):
        output_path = tmp_path / "episode.mp3"

        with patch("audio_utils.urlopen", return_value=mock_urlopen_response) as mock_urlopen:
            download_audio_file("https://example.com/episode.mp3", output_path, timeout_seconds=30)

        mock_urlopen.assert_called_once_with("https://example.com/episode.mp3", timeout=30)
