import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def mock_episode_s3_uri():
    return "s3://test-bucket/07/88/"


@pytest.fixture
def mock_read_metadata_response():
    return {
        "audio_link": "https://example.com/audio.mp3",
        "title": "Test Episode",
        "description": "A test episode for unit testing.",
    }


@pytest.fixture
def mock_urlopen_response():
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read.return_value = b""
    return mock_response
