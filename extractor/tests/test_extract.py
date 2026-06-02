"""Unit tests for extract module (database and RSS feed extraction)."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import extract  # noqa: E402
import pytest


class TestInsertPodcast:
    """Tests for insert_podcast function."""

    def test_insert_podcast_with_valid_rss_url_succeeds(self, make_conn):
        """Verify insert_podcast inserts and commits when URL is valid."""
        conn, cursor = make_conn()
        rss_url = "https://example.com/podcast/feed.xml"

        extract.insert_podcast(conn, rss_url)

        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_insert_podcast_extracts_title_from_rss_url(self, make_conn):
        """Verify podcast title is extracted from RSS URL path."""
        conn, cursor = make_conn()
        rss_url = "https://example.com/my-awesome-podcast/feed.xml"

        extract.insert_podcast(conn, rss_url)

        call_args = cursor.execute.call_args[0]
        assert "my-awesome-podcast" in call_args[1]

    def test_insert_podcast_raises_when_rss_url_empty(self, make_conn):
        """Verify insert_podcast raises ValueError when URL is empty."""
        conn, _ = make_conn()
        with pytest.raises(ValueError, match="RSS URL must be a non-empty string"):
            extract.insert_podcast(conn, "")

    def test_insert_podcast_raises_when_rss_url_not_string(self, make_conn):
        """Verify insert_podcast raises ValueError when URL is not a string."""
        conn, _ = make_conn()
        with pytest.raises(ValueError, match="RSS URL must be a non-empty string"):
            extract.insert_podcast(conn, None)  # type: ignore[invalid-argument-type]

    def test_insert_podcast_rolls_back_on_db_error(self, make_conn):
        """Verify insert_podcast rolls back transaction on database error."""
        conn, cursor = make_conn()
        cursor.execute.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError):
            extract.insert_podcast(conn, "https://example.com/feed.xml")

        conn.rollback.assert_called_once()


class TestGetPodcastsFromDatabase:
    """Tests for get_podcasts_from_database function."""

    def test_get_podcasts_returns_rows_when_present(self, make_conn):
        """Verify get_podcasts_from_database returns fetched rows."""
        rows = [{"id": 1, "title": "Pod A", "rss_url": "https://a.com/feed.xml"}]
        conn, cursor = make_conn(rows=rows)

        result = extract.get_podcasts_from_database(conn)

        assert result == rows
        conn.commit.assert_called_once()

    def test_get_podcasts_returns_empty_list_when_no_podcasts(self, make_conn):
        """Verify get_podcasts_from_database returns empty list when no rows exist."""
        conn, _ = make_conn(rows=[])

        result = extract.get_podcasts_from_database(conn)

        assert result == []
        conn.commit.assert_called_once()

    def test_get_podcasts_executes_select_query(self, make_conn):
        """Verify get_podcasts_from_database executes correct SELECT query."""
        conn, cursor = make_conn(rows=[])

        extract.get_podcasts_from_database(conn)

        cursor.execute.assert_called_once()
        call_args = cursor.execute.call_args[0][0]
        assert "SELECT" in call_args
        assert "podcast_id" in call_args

    def test_get_podcasts_commits_after_fetch(self, make_conn):
        """Verify get_podcasts_from_database commits transaction after fetching."""
        conn, _ = make_conn(rows=[])

        extract.get_podcasts_from_database(conn)

        conn.commit.assert_called_once()

    def test_get_podcasts_rolls_back_on_query_error(self, make_conn):
        """Verify get_podcasts_from_database rolls back on database error."""
        conn, cursor = make_conn(rows=[])
        cursor.execute.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError):
            extract.get_podcasts_from_database(conn)

        conn.rollback.assert_called_once()


class TestGetLatestEpisodeDateFromPodcast:
    """Tests for get_latest_episode_date_from_podcast function."""

    def test_get_latest_date_returns_pub_date_when_episode_exists(self, make_conn):
        """Verify get_latest_episode_date returns publication date when episodes exist."""
        pub = datetime(2026, 5, 1)
        conn, _ = make_conn(fetchone_result={"pub_date": pub})

        result = extract.get_latest_episode_date_from_podcast(conn, podcast_id=1)

        assert result == pub
        conn.commit.assert_called_once()

    def test_get_latest_date_returns_none_when_no_episodes(self, make_conn):
        """Verify get_latest_episode_date returns None when no episodes exist."""
        conn, _ = make_conn(fetchone_result=None)

        result = extract.get_latest_episode_date_from_podcast(conn, podcast_id=1)

        assert result is None
        conn.commit.assert_called_once()

    def test_get_latest_date_raises_when_podcast_id_not_int(self, make_conn):
        """Verify get_latest_episode_date raises ValueError for non-int podcast_id."""
        conn, _ = make_conn()

        with pytest.raises(ValueError, match="Podcast ID must be a non-empty integer"):
            extract.get_latest_episode_date_from_podcast(conn, podcast_id="bad")  # type: ignore[invalid-argument-type]

    def test_get_latest_date_rolls_back_on_query_error(self, make_conn):
        """Verify get_latest_episode_date rolls back transaction on database error."""
        conn, cursor = make_conn(fetchone_result=None)
        cursor.execute.side_effect = RuntimeError("db error")

        with pytest.raises(RuntimeError):
            extract.get_latest_episode_date_from_podcast(conn, podcast_id=1)

        conn.rollback.assert_called_once()


class TestGetNewEpisodesForPodcast:
    """Tests for get_new_episodes_for_podcast function."""

    @patch("extract.get_latest_episode_date_from_podcast")
    @patch("extract.get_episodes_from_rss")
    def test_new_episodes_capped_at_15_when_no_history(self, mock_rss, mock_latest, rss_episode):
        """Verify new episodes are capped at 15 when podcast has no prior episodes."""
        mock_latest.return_value = None
        episodes = [rss_episode(2026, 5, i % 28 + 1, f"ep-{i}") for i in range(20)]
        mock_rss.return_value = episodes
        conn = MagicMock()

        result = extract.get_new_episodes_for_podcast(
            conn, {"podcast_id": 1, "title": "T", "rss_url": "x"}
        )

        assert len(result) == 15

    @patch("extract.get_latest_episode_date_from_podcast")
    @patch("extract.get_episodes_from_rss")
    def test_new_episodes_filters_before_latest_date(self, mock_rss, mock_latest, rss_episode):
        """Verify new episodes only includes episodes after latest stored episode."""
        mock_latest.return_value = datetime(2026, 5, 10)
        mock_rss.return_value = [
            rss_episode(2026, 5, 8, "old"),
            rss_episode(2026, 5, 10, "same-day"),
            rss_episode(2026, 5, 12, "new"),
        ]
        conn = MagicMock()

        result = extract.get_new_episodes_for_podcast(
            conn, {"podcast_id": 2, "title": "T", "rss_url": "x"}
        )

        assert len(result) == 1
        assert result[0]["title"] == "new"

    @patch("extract.get_latest_episode_date_from_podcast", return_value=None)
    @patch("extract.get_episodes_from_rss")
    def test_new_episodes_skips_episodes_with_invalid_date(
        self, mock_rss, mock_latest, rss_episode
    ):
        """Verify new episodes skips entries with missing or invalid publication dates."""
        bad = {"title": "bad", "published_parsed": None}
        good = rss_episode(2026, 5, 20, "good")
        mock_rss.return_value = [bad, good]
        conn = MagicMock()

        result = extract.get_new_episodes_for_podcast(
            conn, {"podcast_id": 3, "title": "T", "rss_url": "x"}
        )

        assert len(result) == 1
        assert result[0]["title"] == "good"


class TestExtractNewEpisodes:
    """Tests for extract_new_episodes orchestration function."""

    PODCASTS = [
        {"podcast_id": 1, "title": "A", "rss_url": "https://a.com/feed.xml"},
        {"podcast_id": 2, "title": "B", "rss_url": "https://b.com/feed.xml"},
    ]

    @patch("extract.get_podcasts_from_database")
    @patch("extract.get_new_episodes_for_podcast")
    def test_extract_returns_data_for_all_podcasts(self, mock_episodes, mock_podcasts, rss_episode):
        """Verify extract_new_episodes returns extracted data for all podcasts."""
        mock_podcasts.return_value = self.PODCASTS
        mock_episodes.return_value = [rss_episode(2026, 5, 1)]
        conn = MagicMock()

        result = extract.extract_new_episodes(conn)

        assert len(result) == 2
        assert result[0]["podcast_id"] == 1
        assert result[1]["podcast_id"] == 2

    @patch("extract.get_podcasts_from_database")
    @patch("extract.get_new_episodes_for_podcast")
    def test_extract_skips_failed_podcast_continues_extraction(
        self, mock_episodes, mock_podcasts, rss_episode
    ):
        """Verify extract_new_episodes continues processing after podcast failure."""
        mock_podcasts.return_value = self.PODCASTS

        def _side_effect(_conn, podcast):
            if podcast["podcast_id"] == 2:
                raise RuntimeError("rss error")
            return [rss_episode(2026, 5, 1)]

        mock_episodes.side_effect = _side_effect
        conn = MagicMock()

        result = extract.extract_new_episodes(conn)

        assert len(result) == 1
        assert result[0]["podcast_id"] == 1
