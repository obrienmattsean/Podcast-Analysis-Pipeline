"""Transform helpers for converting RSS entries into typed models."""

import logging
from datetime import datetime

from model import ValidatedEpisode
from pydantic import HttpUrl, ValidationError


def get_audio_link_from_entry(entry: dict) -> str:
    """Extract the first audio link from an RSS entry.

    Args:
        entry (dict): RSS entry payload.

    Returns:
        str: First audio URL found in links.

    Raises:
        ValueError: If entry is not a dictionary.
    """

    if not isinstance(entry, dict):
        raise ValueError("Entry must be a dictionary.")

    links = entry.get("links", [])
    for link in links:
        if link.get("type", "").startswith("audio/"):
            audio_link = link.get("href")
            logging.debug("Found audio link: %s", audio_link)
            return audio_link
    raise ValueError("No audio link found in entry")


def parse_episode(episode: dict, podcast_id: int) -> ValidatedEpisode:
    """Parse an RSS entry into a validated episode model.

    Args:
        episode (dict): RSS entry payload.
        podcast_id (int): Podcast identifier.

    Returns:
        ValidatedEpisode: Validated typed episode model.

    Raises:
        ValueError: If podcast_id is invalid or published date is missing.
    """

    if not isinstance(podcast_id, int):
        raise ValueError("podcast_id must be an integer")

    if not episode.get("published_parsed"):
        raise ValueError("Episode missing published date")

    published_at = datetime(*episode["published_parsed"][:6])
    title = episode.get("title", "").strip()

    logging.debug(
        "Parsing episode podcast_id=%s title=%s published_at=%s",
        podcast_id,
        title,
        published_at,
    )

    return ValidatedEpisode(
        podcast_id=podcast_id,
        title=title,
        audio_link=HttpUrl(get_audio_link_from_entry(episode)),
        published_at=published_at,
        duration_seconds=episode.get("itunes_duration"),
    )


def transform_episodes_for_podcast(podcast_episodes_data: dict) -> list[ValidatedEpisode]:
    """Transforms all episodes for a podcast.

    Takes extracted podcast data with raw episodes from RSS and validates
    all episodes, returning clean data ready for uploading.

    Args:
        podcast_episodes_data: Dictionary with structure:
                      {
                          'podcast_id': int,
                          'podcast_name': str,
                          'episodes': list[dict]  # Raw RSS episode data
                      }

    Returns:
        list[ValidatedEpisode]: Transformed podcast data with validated episodes.

    Raises:
        ValueError: If podcast_episodes_data is invalid
    """

    podcast_id = podcast_episodes_data.get("podcast_id")
    podcast_title = podcast_episodes_data.get("podcast_title", "unknown")
    raw_episodes = podcast_episodes_data.get("new_episodes", [])

    if not isinstance(podcast_id, int):
        logging.error("Invalid or missing podcast_id=%s, skipping transform", podcast_id)
        return []

    logging.info(
        "Transforming episodes for podcast id=%s title=%s count=%d",
        podcast_id,
        podcast_title,
        len(raw_episodes),
    )

    transformed_episodes = []
    for raw_episode in raw_episodes:
        try:
            parsed = parse_episode(raw_episode, podcast_id=podcast_id)
            transformed_episodes.append(parsed)
        except (ValueError, ValidationError):
            logging.exception(
                "Failed to parse episode for podcast id=%s title=%s",
                podcast_id,
                podcast_title,
            )
            continue

    logging.info(
        "Transformed episodes for podcast id=%s title=%s successful=%d failed=%d",
        podcast_id,
        podcast_title,
        len(transformed_episodes),
        len(raw_episodes) - len(transformed_episodes),
    )
    return transformed_episodes


def transform_all_podcast_episodes(podcast_episodes_list: list[dict]) -> list[dict]:
    """Transforms episodes for all podcasts.

    Main orchestration function that transforms extracted episodes
    from all podcasts.

    Args:
        podcast_episodes_list: List of podcast episode data dictionaries with structure:
                              {
                                  'podcast_id': int,
                                  'podcast_title': str,
                                  'new_episodes': list[dict]  # Raw RSS episode data
                              }

    Returns:
        list: List of transformed podcast data, each containing validated episodes:
                {
                    'podcast_id': int,
                    'podcast_title': str,
                    'new_episodes': list[ValidatedEpisode]
                }

    Raises:
        ValueError: If input is not a list
    """
    if not isinstance(podcast_episodes_list, list):
        raise ValueError("Input must be a list of podcast data.")

    logging.info(
        "Starting transform for %d podcasts",
        len(podcast_episodes_list),
    )

    transformed_all = []
    for podcast_data in podcast_episodes_list:
        try:
            transformed_episodes = transform_episodes_for_podcast(podcast_data)
            transformed_data = {
                "podcast_id": podcast_data.get("podcast_id"),
                "podcast_title": podcast_data.get("podcast_title"),
                "new_episodes": transformed_episodes,
            }
            transformed_all.append(transformed_data)
        except Exception:
            logging.exception(
                "Failed to transform episodes for podcast title=%s",
                podcast_data.get("podcast_title", "unknown"),
            )

    total_transformed = sum(len(p.get("new_episodes") or []) for p in transformed_all)
    logging.info(
        "Transform complete. Processed podcasts=%d total_episodes=%d",
        len(podcast_episodes_list),
        total_transformed,
    )
    return transformed_all
