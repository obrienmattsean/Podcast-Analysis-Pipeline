"""Pytest configuration and fixtures for extractor tests."""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model import ValidatedEpisode


@pytest.fixture
def make_conn():
    """Factory fixture for mocking psycopg2 connections and cursors.

    Returns a callable that creates (conn, cursor) tuple with realistic psycopg2 mock behavior.
    Supports customizing fetchall and fetchone return values for test scenarios.

    Returns:
        Callable: Factory function that accepts rows and fetchone_result kwargs.

    Example:
        conn, cursor = make_conn(rows=[{"id": 1}])
        conn, cursor = make_conn(fetchone_result={"pub_date": datetime(2026, 5, 1)})
    """

    def _factory(rows=None, fetchone_result=None):
        cursor = MagicMock()
        cursor.fetchall.return_value = rows or []
        cursor.fetchone.return_value = fetchone_result

        # Mock context manager for 'with conn.cursor() as cursor:' pattern
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=cursor)
        ctx.__exit__ = MagicMock(return_value=False)

        conn = MagicMock()
        conn.cursor.return_value = ctx
        return conn, cursor

    return _factory


@pytest.fixture
def rss_episode():
    """Factory fixture for minimal RSS episode dictionaries.

    Creates RSS entry dictionaries with published_parsed tuple format expected by feedparser.

    Returns:
        Callable: Factory function that accepts year, month, day, title parameters.

    Example:
        episode = rss_episode(2026, 5, 15, "Episode Title")
    """

    def _factory(year, month, day, title="ep"):
        return {
            "title": title,
            "published_parsed": (year, month, day, 0, 0, 0, 0, 0, 0),
        }

    return _factory


@pytest.fixture
def rss_episode_with_audio():
    """Factory fixture for RSS episode dictionaries with audio links.

    Creates RSS entries with audio/mpeg links suitable for episode extraction tests.

    Returns:
        Callable: Factory function with year, month, day, title, audio_url parameters.

    Example:
        episode = rss_episode_with_audio(2026, 5, 15, "Episode", "https://example.com/ep.mp3")
    """

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
    """Factory fixture for ValidatedEpisode Pydantic models.

    Creates fully validated episode models ready for database insertion or S3 upload.

    Returns:
        Callable: Factory function with podcast_id, title, audio_link, published_at parameters.

    Example:
        episode = validated_episode(podcast_id=1, title="My Episode")
        episode = validated_episode(published_at=datetime(2026, 6, 1))
    """

    def _factory(
        podcast_id=1,
        title="Test Episode",
        audio_link: str = "https://example.com/ep.mp3",
        published_at=None,
    ):
        if published_at is None:
            published_at = datetime(2026, 5, 1)
        return ValidatedEpisode(
            podcast_id=podcast_id,
            title=title,
            audio_link=HttpUrl(audio_link),
            published_at=published_at,
        )

    return _factory
