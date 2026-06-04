import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from db_functions import (
    format_last_updated,
    format_time_since_published,
    format_tracked_since,
    get_all_podcasts,
    get_recent_episodes,
    trigger_pipeline,
)


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


@pytest.mark.parametrize(
    "last_updated, expected",
    [
        (datetime.now() - timedelta(hours=2), "2h ago"),
        (datetime.now() - timedelta(hours=0), "0h ago"),
        (datetime.now() - timedelta(hours=23), "23h ago"),
        (datetime.now() - timedelta(hours=25), "yesterday"),
        (datetime.now() - timedelta(hours=47), "yesterday"),
        (datetime.now() - timedelta(days=3), "3d ago"),
        (None, "never"),
    ],
)
def test_format_last_updated_returns_expected_string(
    last_updated: datetime | None, expected: str
) -> None:
    result = format_last_updated(last_updated)

    assert result == expected


def test_get_all_podcasts_with_no_rows_returns_empty_list(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

    result = get_all_podcasts(mock_conn)

    assert result == []


def test_get_all_podcasts_maps_rows_to_expected_dict_fields(mock_conn: MagicMock) -> None:
    tracked_date = datetime(2024, 3, 10)
    last_updated_date = datetime(2024, 6, 1)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("The Daily", 42, 0.35, tracked_date, last_updated_date, 7),
    ]

    result = get_all_podcasts(mock_conn)

    assert len(result) == 1
    assert result[0]["podcast_title"] == "The Daily"
    assert result[0]["num_episodes"] == 42
    assert result[0]["avg_sentiment_score"] == 0.35
    assert result[0]["tracked_since"] == tracked_date
    assert result[0]["last_updated"] == last_updated_date
    assert result[0]["podcast_id"] == 7


def test_get_all_podcasts_returns_all_rows(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("Podcast A", 10, 0.1, datetime(2024, 1, 1), datetime(2024, 3, 1), 1),
        ("Podcast B", 5, -0.2, datetime(2023, 6, 15), datetime(2024, 2, 1), 2),
    ]

    result = get_all_podcasts(mock_conn)
    assert len(result) == 2
    assert result[0]["podcast_title"] == "Podcast A"
    assert result[1]["podcast_title"] == "Podcast B"


# ---------------------------------------------------------------------------
# trigger_pipeline
# ---------------------------------------------------------------------------


def test_trigger_pipeline_with_valid_arn_returns_execution_arn() -> None:
    mock_response = {"executionArn": "arn:aws:states:eu-west-2:123:execution:pipeline:abc"}
    env = {"STEP_FUNCTION_ARN": "arn:aws:states:eu-west-2:123:stateMachine:pipeline"}

    with (
        patch.dict("os.environ", env),
        patch("db_functions.boto3.client") as mock_client,
    ):
        mock_client.return_value.start_execution.return_value = mock_response
        result = trigger_pipeline("https://example.com/feed.rss")

    assert result == mock_response["executionArn"]


def test_trigger_pipeline_passes_rss_url_in_input() -> None:
    mock_response = {"executionArn": "arn:aws:states:eu-west-2:123:execution:pipeline:abc"}
    rss_url = "https://example.com/feed.rss"
    env = {"STEP_FUNCTION_ARN": "arn:aws:states:eu-west-2:123:stateMachine:pipeline"}

    with (
        patch.dict("os.environ", env),
        patch("db_functions.boto3.client") as mock_client,
    ):
        mock_client.return_value.start_execution.return_value = mock_response
        trigger_pipeline(rss_url)

    call_kwargs = mock_client.return_value.start_execution.call_args[1]
    assert json.loads(call_kwargs["input"]) == {"rss_url": rss_url}


def test_trigger_pipeline_without_arn_env_var_raises_environment_error() -> None:
    with (
        patch.dict("os.environ", {"STEP_FUNCTION_ARN": ""}, clear=False),
        pytest.raises(EnvironmentError, match="STEP_FUNCTION_ARN"),
    ):
        trigger_pipeline("https://example.com/feed.rss")


# ---------------------------------------------------------------------------
# get_recent_episodes
# ---------------------------------------------------------------------------


def test_get_recent_episodes_with_no_rows_returns_empty_list(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

    result = get_recent_episodes(mock_conn)

    assert result == []


def test_get_recent_episodes_maps_row_to_expected_dict_fields(mock_conn: MagicMock) -> None:
    pub_date = datetime.now() - timedelta(hours=3)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("Test Podcast", "Test Episode", pub_date, "A summary.", 0.7, False, ["AI", "Tech"]),
    ]

    result = get_recent_episodes(mock_conn)

    assert len(result) == 1
    ep = result[0]
    assert ep["podcast_title"] == "Test Podcast"
    assert ep["episode_title"] == "Test Episode"
    assert ep["summary"] == "A summary."
    assert ep["sentiment_score"] == 0.7
    assert ep["flagged"] is False
    assert ep["keywords"] == ["AI", "Tech"]


def test_get_recent_episodes_includes_keywords_field(mock_conn: MagicMock) -> None:
    pub_date = datetime.now() - timedelta(days=1)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("Podcast", "Episode", pub_date, None, None, False, ["Python", "Cloud"]),
    ]

    result = get_recent_episodes(mock_conn)

    assert "keywords" in result[0]
    assert result[0]["keywords"] == ["Python", "Cloud"]


def test_get_recent_episodes_with_empty_keywords_returns_empty_list(mock_conn: MagicMock) -> None:
    pub_date = datetime.now() - timedelta(hours=1)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("Podcast", "Episode", pub_date, None, None, False, []),
    ]

    result = get_recent_episodes(mock_conn)

    assert result[0]["keywords"] == []


def test_get_recent_episodes_passes_limit_to_query(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

    get_recent_episodes(mock_conn, limit=5)

    cursor = mock_conn.cursor.return_value.__enter__.return_value
    executed_params = cursor.execute.call_args[0][1]
    assert executed_params == (5,)


# ---------------------------------------------------------------------------
# get_sentiment_over_time
# ---------------------------------------------------------------------------


def test_get_sentiment_over_time_with_no_rows_returns_empty_list(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

    result = get_sentiment_over_time(mock_conn, podcast_id=1)

    assert result == []


def test_get_sentiment_over_time_maps_rows_to_expected_dict_fields(
    mock_conn: MagicMock,
) -> None:
    pub_date = datetime(2024, 5, 10)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        (pub_date, 0.65),
    ]

    result = get_sentiment_over_time(mock_conn, podcast_id=3)

    assert len(result) == 1
    assert result[0]["pub_date"] == pub_date
    assert result[0]["sentiment_score"] == 0.65


def test_get_sentiment_over_time_returns_all_rows(mock_conn: MagicMock) -> None:
    rows = [
        (datetime(2024, 1, 1), 0.1),
        (datetime(2024, 2, 1), -0.3),
        (datetime(2024, 3, 1), 0.7),
    ]
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = rows

    result = get_sentiment_over_time(mock_conn, podcast_id=5)

    assert len(result) == 3


def test_get_sentiment_over_time_passes_podcast_id_to_query(mock_conn: MagicMock) -> None:
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = []

    get_sentiment_over_time(mock_conn, podcast_id=42)

    cursor = mock_conn.cursor.return_value.__enter__.return_value
    executed_params = cursor.execute.call_args[0][1]
    assert executed_params == (42,)


def test_get_sentiment_over_time_handles_none_sentiment_score(mock_conn: MagicMock) -> None:
    pub_date = datetime(2024, 4, 1)
    mock_conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        (pub_date, None),
    ]

    result = get_sentiment_over_time(mock_conn, podcast_id=1)

    assert result[0]["sentiment_score"] is None
