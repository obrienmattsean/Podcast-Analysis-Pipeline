import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "extractor"))

from model import ValidatedEpisode


@pytest.fixture
def make_conn():
    """Factory fixture: returns a (conn, cursor) pair that mimics psycopg2."""

    def _factory(rows=None, fetchone_result=None):
        cursor = MagicMock()
        cursor.fetchall.return_value = rows or []
        cursor.fetchone.return_value = fetchone_result

        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=cursor)
        ctx.__exit__ = MagicMock(return_value=False)

        conn = MagicMock()
        conn.cursor.return_value = ctx
        return conn, cursor

    return _factory


@pytest.fixture
def rss_episode():
    """Factory fixture: builds a minimal RSS episode dict."""

    def _factory(year, month, day, title="ep"):
        return {
            "title": title,
            "published_parsed": (year, month, day, 0, 0, 0, 0, 0, 0),
        }

    return _factory


@pytest.fixture
def rss_episode_with_audio():
    """Factory fixture: builds an RSS episode with audio link."""

    def _factory(year, month, day, title="ep", audio_url="https://example.com/ep.mp3"):
        return {
            "title": title,
            "published_parsed": (year, month, day, 0, 0, 0, 0, 0, 0),
            "links": [
                {"type": "audio/mpeg", "href": audio_url},
            ],
        }

    return _factory


@pytest.fixture
def validated_episode():
    """Factory fixture: builds a ValidatedEpisode model."""

    def _factory(
        podcast_id=1,
        title="Test Episode",
        audio_link="https://example.com/ep.mp3",
        published_at=None,
    ):
        if published_at is None:
            published_at = datetime(2026, 5, 1)
        return ValidatedEpisode(
            podcast_id=podcast_id,
            title=title,
            audio_link=audio_link,
            published_at=published_at,
        )

    return _factory
