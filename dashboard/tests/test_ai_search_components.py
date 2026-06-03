"""Tests for ai_search_components.py – pure data-processing functions."""

import pytest
from ai_search_components import process_chunks

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def single_chunk() -> list[dict]:
    return [
        {
            "podcast_title": "Tech Talk",
            "episode_title": "AI in 2025",
            "chunk_transcript": "Some text",
            "similarity": 0.85,
        }
    ]


@pytest.fixture
def multi_chunk_same_episode() -> list[dict]:
    return [
        {
            "podcast_title": "Tech Talk",
            "episode_title": "AI in 2025",
            "chunk_transcript": "First mention",
            "similarity": 0.90,
        },
        {
            "podcast_title": "Tech Talk",
            "episode_title": "AI in 2025",
            "chunk_transcript": "Second mention",
            "similarity": 0.80,
        },
    ]


@pytest.fixture
def multi_chunk_multiple_podcasts() -> list[dict]:
    return [
        {
            "podcast_title": "Tech Talk",
            "episode_title": "Episode 1",
            "chunk_transcript": "Text A",
            "similarity": 0.9,
        },
        {
            "podcast_title": "Business Weekly",
            "episode_title": "Episode 2",
            "chunk_transcript": "Text B",
            "similarity": 0.75,
        },
        {
            "podcast_title": "Tech Talk",
            "episode_title": "Episode 3",
            "chunk_transcript": "Text C",
            "similarity": 0.65,
        },
    ]


# ---------------------------------------------------------------------------
# process_chunks
# ---------------------------------------------------------------------------


def test_process_chunks_with_empty_list_returns_zero_podcasts_and_empty_episodes() -> None:
    num_podcasts, episodes = process_chunks([])

    assert num_podcasts == 0
    assert episodes == {}


def test_process_chunks_with_single_chunk_returns_one_podcast(
    single_chunk: list[dict],
) -> None:
    num_podcasts, _ = process_chunks(single_chunk)

    assert num_podcasts == 1


def test_process_chunks_with_single_chunk_creates_one_episode(
    single_chunk: list[dict],
) -> None:
    _, episodes = process_chunks(single_chunk)

    assert len(episodes) == 1


def test_process_chunks_groups_chunks_from_same_episode(
    multi_chunk_same_episode: list[dict],
) -> None:
    _, episodes = process_chunks(multi_chunk_same_episode)

    assert len(episodes) == 1


def test_process_chunks_counts_mentions_per_episode(
    multi_chunk_same_episode: list[dict],
) -> None:
    _, episodes = process_chunks(multi_chunk_same_episode)

    episode = list(episodes.values())[0]
    assert episode["count"] == 2


def test_process_chunks_stores_all_chunks_on_episode(
    multi_chunk_same_episode: list[dict],
) -> None:
    _, episodes = process_chunks(multi_chunk_same_episode)

    episode = list(episodes.values())[0]
    assert len(episode["chunks"]) == 2


def test_process_chunks_counts_unique_podcasts(
    multi_chunk_multiple_podcasts: list[dict],
) -> None:
    num_podcasts, _ = process_chunks(multi_chunk_multiple_podcasts)

    assert num_podcasts == 2


def test_process_chunks_creates_separate_episode_per_unique_podcast_episode_pair(
    multi_chunk_multiple_podcasts: list[dict],
) -> None:
    _, episodes = process_chunks(multi_chunk_multiple_podcasts)

    assert len(episodes) == 3


def test_process_chunks_uses_unknown_for_missing_podcast_title() -> None:
    chunks = [{"episode_title": "EP1", "chunk_transcript": "text", "similarity": 0.8}]

    _, episodes = process_chunks(chunks)

    episode = list(episodes.values())[0]
    assert episode["podcast"] == "Unknown"


def test_process_chunks_uses_unknown_for_missing_episode_title() -> None:
    chunks = [{"podcast_title": "Pod", "chunk_transcript": "text", "similarity": 0.8}]

    _, episodes = process_chunks(chunks)

    episode = list(episodes.values())[0]
    assert episode["episode"] == "Unknown"


@pytest.mark.parametrize("num_chunks", [1, 3, 5])
def test_process_chunks_count_matches_number_of_input_chunks_for_same_episode(
    num_chunks: int,
) -> None:
    chunks = [
        {
            "podcast_title": "Pod",
            "episode_title": "EP1",
            "chunk_transcript": f"text {i}",
            "similarity": 0.8,
        }
        for i in range(num_chunks)
    ]

    _, episodes = process_chunks(chunks)

    episode = list(episodes.values())[0]
    assert episode["count"] == num_chunks
