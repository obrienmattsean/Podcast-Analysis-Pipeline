"""Tests for rag/generator.py – context building and response generation."""

from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAIError
from rag.generator import answer_query, build_context, generate_response

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_openai_client() -> MagicMock:
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = "This is a generated answer."
    client.chat.completions.create.return_value.choices = [choice]
    return client


@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {
            "episode_title": "Episode 1",
            "podcast_title": "Podcast A",
            "chunk_transcript": "Nike discussed sustainability at a conference.",
            "similarity": 0.92,
        },
        {
            "episode_title": "Episode 2",
            "podcast_title": "Podcast B",
            "chunk_transcript": "Brands need to invest in green initiatives.",
            "similarity": 0.78,
        },
    ]


# ---------------------------------------------------------------------------
# build_context
# ---------------------------------------------------------------------------


def test_build_context_with_chunks_includes_episode_title(
    sample_chunks: list[dict],
) -> None:
    result = build_context(sample_chunks)

    assert "Episode 1" in result
    assert "Episode 2" in result


def test_build_context_with_chunks_includes_podcast_title(
    sample_chunks: list[dict],
) -> None:
    result = build_context(sample_chunks)

    assert "Podcast A" in result
    assert "Podcast B" in result


def test_build_context_with_chunks_includes_transcript_text(
    sample_chunks: list[dict],
) -> None:
    result = build_context(sample_chunks)

    assert "Nike discussed sustainability" in result


def test_build_context_formats_similarity_to_two_decimal_places(
    sample_chunks: list[dict],
) -> None:
    result = build_context(sample_chunks)

    assert "0.92" in result


def test_build_context_when_similarity_is_none_shows_na() -> None:
    chunks = [
        {
            "episode_title": "EP",
            "podcast_title": "Pod",
            "chunk_transcript": "text",
            "similarity": None,
        }
    ]

    result = build_context(chunks)

    assert "N/A" in result


def test_build_context_with_empty_list_returns_empty_string() -> None:
    result = build_context([])

    assert result == ""


# ---------------------------------------------------------------------------
# generate_response
# ---------------------------------------------------------------------------


def test_generate_response_returns_string_from_api(mock_openai_client: MagicMock) -> None:
    result = generate_response(mock_openai_client, "What is AI?", "Some context")

    assert result == "This is a generated answer."


def test_generate_response_calls_chat_completions_with_system_prompt(
    mock_openai_client: MagicMock,
) -> None:
    generate_response(mock_openai_client, "query", "context")

    call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    roles = [m["role"] for m in messages]
    assert "system" in roles
    assert "user" in roles


def test_generate_response_includes_user_query_in_prompt(
    mock_openai_client: MagicMock,
) -> None:
    generate_response(mock_openai_client, "sustainability trends", "context")

    call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    user_message = next(m for m in call_kwargs["messages"] if m["role"] == "user")
    assert "sustainability trends" in user_message["content"]


def test_generate_response_when_no_choices_returns_fallback(
    mock_openai_client: MagicMock,
) -> None:
    mock_openai_client.chat.completions.create.return_value.choices = []

    with pytest.raises(ValueError, match="No response choices"):
        generate_response(mock_openai_client, "query", "context")


def test_generate_response_when_api_raises_propagates_error(
    mock_openai_client: MagicMock,
) -> None:
    mock_openai_client.chat.completions.create.side_effect = OpenAIError("quota exceeded")

    with pytest.raises(OpenAIError):
        generate_response(mock_openai_client, "query", "context")


def test_generate_response_when_content_is_none_returns_fallback(
    mock_openai_client: MagicMock,
) -> None:
    mock_openai_client.chat.completions.create.return_value.choices[0].message.content = None

    result = generate_response(mock_openai_client, "query", "context")

    assert "could not generate" in result.lower()


# ---------------------------------------------------------------------------
# answer_query
# ---------------------------------------------------------------------------


def test_answer_query_when_no_chunks_found_returns_no_info_message() -> None:
    with (
        patch("rag.generator.get_openai_client") as mock_get_client,
        patch("rag.generator.get_db_connection") as mock_get_conn,
        patch("rag.generator.get_query_embedding", return_value=[0.1] * 1536),
        patch("rag.generator.query_similar_chunks", return_value=[]),
    ):
        mock_get_client.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        result = answer_query("some query")

        assert "couldn't find" in result.lower()
        mock_conn.close.assert_called_once()


def test_answer_query_closes_db_connection_on_success() -> None:
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "answer"

    with (
        patch("rag.generator.get_openai_client") as mock_get_client,
        patch("rag.generator.get_db_connection") as mock_get_conn,
        patch("rag.generator.get_query_embedding", return_value=[0.1] * 1536),
        patch(
            "rag.generator.query_similar_chunks",
            return_value=[
                {
                    "episode_title": "EP",
                    "podcast_title": "Pod",
                    "chunk_transcript": "text",
                    "similarity": 0.8,
                }
            ],
        ),
        patch("rag.generator.generate_response", return_value="answer"),
    ):
        mock_get_client.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        answer_query("some query")

        mock_conn.close.assert_called_once()


def test_answer_query_closes_db_connection_on_exception() -> None:
    with (
        patch("rag.generator.get_openai_client") as mock_get_client,
        patch("rag.generator.get_db_connection") as mock_get_conn,
        patch("rag.generator.get_query_embedding", side_effect=RuntimeError("embed failed")),
    ):
        mock_get_client.return_value = MagicMock()
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        with pytest.raises(RuntimeError):
            answer_query("some query")

        mock_conn.close.assert_called_once()
