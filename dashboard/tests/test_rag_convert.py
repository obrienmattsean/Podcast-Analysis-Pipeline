"""Tests for rag/convert.py – query embedding conversion."""

from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError
from rag.convert import get_openai_client, get_query_embedding

# ---------------------------------------------------------------------------
# get_openai_client
# ---------------------------------------------------------------------------


def test_get_openai_client_when_api_key_set_returns_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch("rag.convert.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        client = get_openai_client()

    mock_openai.assert_called_once_with(api_key="test-key")
    assert client is not None


def test_get_openai_client_when_api_key_missing_raises_value_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        get_openai_client()


# ---------------------------------------------------------------------------
# get_query_embedding
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_openai_client() -> MagicMock:
    client = MagicMock()
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1] * 1536
    client.embeddings.create.return_value.data = [mock_embedding]
    return client


def test_get_query_embedding_returns_list_of_floats(mock_openai_client: MagicMock) -> None:
    result = get_query_embedding(mock_openai_client, "test query")

    assert isinstance(result, list)
    assert len(result) == 1536


def test_get_query_embedding_calls_api_with_correct_params(mock_openai_client: MagicMock) -> None:
    get_query_embedding(mock_openai_client, "my query")

    mock_openai_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small",
        input="my query",
        dimensions=1536,
    )


def test_get_query_embedding_when_api_raises_propagates_error(
    mock_openai_client: MagicMock,
) -> None:
    mock_openai_client.embeddings.create.side_effect = OpenAIError("API failure")

    with pytest.raises(OpenAIError):
        get_query_embedding(mock_openai_client, "query")
