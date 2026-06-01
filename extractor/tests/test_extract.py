from datetime import datetime
from unittest.mock import MagicMock, patch

import extract  # noqa: E402
import pytest


class TestGetPodcastsFromDatabase:
    def test_returns_rows(self, make_conn):
        rows = [{"id": 1, "title": "Pod A", "rss_url": "https://a.com/feed.xml"}]
        conn, cursor = make_conn(rows=rows)

        result = extract.get_podcasts_from_database(conn)

        assert result == rows
        cursor.execute.assert_called_once_with("SELECT id, title, rss_url FROM podcasts")
        conn.commit.assert_called_once()

    def test_returns_empty_when_no_rows(self, make_conn):
        conn, _ = make_conn(rows=[])
        assert extract.get_podcasts_from_database(conn) == []
        conn.commit.assert_called_once()

    def test_rolls_back_when_query_fails(self, make_conn):
        conn, cursor = make_conn(rows=[])
        cursor.execute.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError):
            extract.get_podcasts_from_database(conn)

        conn.rollback.assert_called_once()


class TestGetLatestEpisodeDateFromPodcast:
    def test_returns_pub_date(self, make_conn):
        pub = datetime(2026, 5, 1)
        conn, _ = make_conn(fetchone_result={"pub_date": pub})

        result = extract.get_latest_episode_date_from_podcast(conn, podcast_id=1)

        assert result == pub
        conn.commit.assert_called_once()

    def test_returns_none_when_no_rows(self, make_conn):
        conn, _ = make_conn(fetchone_result=None)
        result = extract.get_latest_episode_date_from_podcast(conn, podcast_id=1)
        assert result is None
        conn.commit.assert_called_once()

    def test_raises_for_non_int_id(self, make_conn):
        conn, _ = make_conn()
        with pytest.raises(ValueError):
            extract.get_latest_episode_date_from_podcast(conn, podcast_id="bad")  # type: ignore[invalid-argument-type]

    def test_rolls_back_when_query_fails(self, make_conn):
        conn, cursor = make_conn(fetchone_result=None)
        cursor.execute.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError):
            extract.get_latest_episode_date_from_podcast(conn, podcast_id=1)

        conn.rollback.assert_called_once()


class TestGetNewEpisodesForPodcast:
    @patch("extract.get_latest_episode_date_from_podcast")
    @patch("extract.get_episodes_from_rss")
    def test_caps_at_15_when_no_history(self, mock_rss, mock_latest, rss_episode):
        mock_latest.return_value = None
        episodes = [rss_episode(2026, 5, i % 28 + 1, f"ep-{i}") for i in range(20)]
        mock_rss.return_value = episodes
        conn = MagicMock()

        result = extract.get_new_episodes_for_podcast(conn, {"id": 1, "title": "T", "rss_url": "x"})

        assert len(result) == 15

    @patch("extract.get_latest_episode_date_from_podcast")
    @patch("extract.get_episodes_from_rss")
    def test_filters_older_than_latest_date(self, mock_rss, mock_latest, rss_episode):
        mock_latest.return_value = datetime(2026, 5, 10)
        mock_rss.return_value = [
            rss_episode(2026, 5, 8, "old"),
            rss_episode(2026, 5, 10, "same-day"),
            rss_episode(2026, 5, 12, "new"),
        ]
        conn = MagicMock()

        result = extract.get_new_episodes_for_podcast(conn, {"id": 2, "title": "T", "rss_url": "x"})

        assert len(result) == 1
        assert result[0]["title"] == "new"

    @patch("extract.get_latest_episode_date_from_podcast", return_value=None)
    @patch("extract.get_episodes_from_rss")
    def test_skips_episodes_with_bad_date(self, mock_rss, mock_latest, rss_episode):
        bad = {"title": "bad", "published_parsed": None}
        good = rss_episode(2026, 5, 20, "good")
        mock_rss.return_value = [bad, good]
        conn = MagicMock()

        result = extract.get_new_episodes_for_podcast(conn, {"id": 3, "title": "T", "rss_url": "x"})

        assert len(result) == 1
        assert result[0]["title"] == "good"


class TestExtractNewEpisodes:
    PODCASTS = [
        {"id": 1, "title": "A", "rss_url": "https://a.com/feed.xml"},
        {"id": 2, "title": "B", "rss_url": "https://b.com/feed.xml"},
    ]

    @patch("extract.get_podcasts_from_database")
    @patch("extract.get_new_episodes_for_podcast")
    def test_returns_all_podcasts(self, mock_episodes, mock_podcasts, rss_episode):
        mock_podcasts.return_value = self.PODCASTS
        mock_episodes.return_value = [rss_episode(2026, 5, 1)]
        conn = MagicMock()

        result = extract.extract_new_episodes(conn)

        assert len(result) == 2
        assert result[0]["podcast_id"] == 1
        assert result[1]["podcast_id"] == 2

    @patch("extract.get_podcasts_from_database")
    @patch("extract.get_new_episodes_for_podcast")
    def test_skips_failed_podcast(self, mock_episodes, mock_podcasts, rss_episode):
        mock_podcasts.return_value = self.PODCASTS

        def _side_effect(_conn, podcast):
            if podcast["id"] == 2:
                raise RuntimeError("rss error")
            return [rss_episode(2026, 5, 1)]

        mock_episodes.side_effect = _side_effect
        conn = MagicMock()

        result = extract.extract_new_episodes(conn)

        assert len(result) == 1
        assert result[0]["podcast_id"] == 1
