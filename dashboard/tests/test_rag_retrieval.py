"""Tests for rag/retrieval.py – database chunk retrieval."""

from unittest.mock import MagicMock, patch

import pytest
from rag.retrieval import get_db_connection, query_similar_chunks

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=conn.cursor.return_value)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def sample_embedding() -> list[float]:
    return [0.1] * 1536


def _make_db_row(
    episode_title: str = "Episode 1",
    podcast_title: str = "Podcast A",
    chunk_index: int = 0,
    transcript: str = "Some transcript text",
    similarity: float = 0.85,
) -> tuple:
    return (episode_title, podcast_title, chunk_index, transcript, similarity)


# ---------------------------------------------------------------------------
# get_db_connection
# ---------------------------------------------------------------------------


def test_get_db_connection_when_env_vars_set_creates_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RDS_HOST", "localhost")
    monkeypatch.setenv("RDS_DBNAME", "testdb")
    monkeypatch.setenv("RDS_USER", "user")
    monkeypatch.setenv("RDS_PASSWORD", "pass")
    monkeypatch.setenv("RDS_PORT", "5432")

    with patch("rag.retrieval.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        conn = get_db_connection()

    mock_connect.assert_called_once_with(
        host="localhost",
        database="testdb",
        user="user",
        password="pass",
        port=5432,
    )
    assert conn is not None


def test_get_db_connection_uses_default_port_when_not_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RDS_HOST", "localhost")
    monkeypatch.setenv("RDS_DBNAME", "testdb")
    monkeypatch.setenv("RDS_USER", "user")
    monkeypatch.setenv("RDS_PASSWORD", "pass")
    monkeypatch.delenv("RDS_PORT", raising=False)

    with patch("rag.retrieval.connect") as mock_connect:
        mock_connect.return_value = MagicMock()
        get_db_connection()

    _, kwargs = mock_connect.call_args
    assert kwargs["port"] == 5432


# ---------------------------------------------------------------------------
# query_similar_chunks
# ---------------------------------------------------------------------------


def test_query_similar_chunks_with_no_rows_returns_empty_list(
    mock_conn: MagicMock,
    sample_embedding: list[float],
) -> None:
    mock_conn.cursor.return_value.fetchall.return_value = []

    result = query_similar_chunks(mock_conn, sample_embedding)

    assert result == []


def test_query_similar_chunks_returns_chunks_above_threshold(
    mock_conn: MagicMock,
    sample_embedding: list[float],
) -> None:
    mock_conn.cursor.return_value.fetchall.return_value = [
        _make_db_row(similarity=0.9),
        _make_db_row(episode_title="Episode 2", similarity=0.6),
        _make_db_row(episode_title="Episode 3", similarity=0.3),
    ]

    result = query_similar_chunks(mock_conn, sample_embedding, similarity_threshold=0.5)

    assert len(result) == 2


def test_query_similar_chunks_filters_out_chunks_below_threshold(
    mock_conn: MagicMock,
    sample_embedding: list[float],
) -> None:
    mock_conn.cursor.return_value.fetchall.return_value = [
        _make_db_row(similarity=0.2),
    ]

    result = query_similar_chunks(mock_conn, sample_embedding, similarity_threshold=0.5)

    assert result == []


def test_query_similar_chunks_maps_row_to_expected_dict_keys(
    mock_conn: MagicMock,
    sample_embedding: list[float],
) -> None:
    mock_conn.cursor.return_value.fetchall.return_value = [
        _make_db_row(
            episode_title="My Episode",
            podcast_title="My Podcast",
            chunk_index=3,
            transcript="Hello world",
            similarity=0.75,
        )
    ]

    result = query_similar_chunks(mock_conn, sample_embedding, similarity_threshold=0.5)

    assert len(result) == 1
    chunk = result[0]
    assert chunk["episode_title"] == "My Episode"
    assert chunk["podcast_title"] == "My Podcast"
    assert chunk["chunk_index"] == 3
    assert chunk["chunk_transcript"] == "Hello world"
    assert chunk["similarity"] == 0.75


@pytest.mark.parametrize("top_k", [3, 10, 25])
def test_query_similar_chunks_passes_top_k_to_sql(
    mock_conn: MagicMock,
    sample_embedding: list[float],
    top_k: int,
) -> None:
    mock_conn.cursor.return_value.fetchall.return_value = []

    query_similar_chunks(mock_conn, sample_embedding, top_k=top_k)

    executed_params = mock_conn.cursor.return_value.execute.call_args[0][1]
    assert top_k in executed_params
