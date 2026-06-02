from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from db_functions import format_time_since_published, format_tracked_since, get_all_podcasts


@pytest.mark.parametrize(
    "pub_date, expected",
    [
        (datetime.now() - timedelta(hours=5), "5 hours ago"),
        (datetime.now() - timedelta(hours=1), "1 hour ago"),
        (datetime.now() - timedelta(hours=23), "23 hours ago"),
        (datetime.now() - timedelta(hours=25), "Yesterday"),
        (datetime.now() - timedelta(hours=47), "Yesterday"),
        (datetime.now() - timedelta(days=2), "2 days ago"),
        (datetime.now() - timedelta(days=10), "10 days ago"),
    ],
)
def test_format_time_since_published(pub_date, expected):
    assert format_time_since_published(pub_date) == expected


@pytest.fixture
def mock_conn() -> MagicMock:
    return MagicMock()


@pytest.mark.parametrize(
    "tracked_since, expected",
    [
        (datetime(2024, 1, 15), "January 15, 2024"),
        (datetime(2023, 6, 1), "June 01, 2023"),
        (None, "N/A"),
    ],
)
def test_format_tracked_since_returns_expected_string(
    tracked_since: datetime | None, expected: str
) -> None:
    result = format_tracked_since(tracked_since)

    assert result == expected


def test_get_all_podcasts_with_no_rows_returns_empty_list(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

    result = get_all_podcasts(mock_conn)

    assert result == []


def test_get_all_podcasts_maps_rows_to_expected_dict_fields(mock_conn: MagicMock) -> None:
    tracked_date = datetime(2024, 3, 10)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("The Daily", 42, 0.35, tracked_date),
    ]

    result = get_all_podcasts(mock_conn)

    assert len(result) == 1
    assert result[0]["podcast_title"] == "The Daily"
    assert result[0]["num_episodes"] == 42
    assert result[0]["avg_sentiment_score"] == 0.35
    assert result[0]["tracked_since"] == tracked_date


def test_get_all_podcasts_returns_all_rows(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("Podcast A", 10, 0.1, datetime(2024, 1, 1)),
        ("Podcast B", 5, -0.2, datetime(2023, 6, 15)),
    ]

    result = get_all_podcasts(mock_conn)

    assert len(result) == 2
    assert result[0]["podcast_title"] == "Podcast A"
    assert result[1]["podcast_title"] == "Podcast B"
