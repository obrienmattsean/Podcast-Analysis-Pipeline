"""Transform helpers for converting RSS entries into typed models."""

import logging
from datetime import datetime
from typing import Optional

from model import ValidatedEpisode
from pydantic import ValidationError


def get_logger() -> None:
    """Configures application logging."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    return logging.getLogger(__name__)


logger = get_logger()


def get_audio_link_from_entry(entry: dict) -> Optional[str]:
    """Extract the first audio link from an RSS entry."""

    if not isinstance(entry, dict):
        raise ValueError("Entry must be a dictionary.")

    links = entry.get("links", [])
    for link in links:
        if link.get("type", "").startswith("audio/"):
            audio_link = link.get("href")
            logger.debug("Found audio link: %s", audio_link)
            return audio_link
    logger.debug("No audio link found in entry, total_links=%d", len(links))
    return None


def parse_episode(episode: dict, podcast_id: int) -> ValidatedEpisode:
    """Convert an RSS entry into a validated ValidatedEpisode model."""

    if not isinstance(podcast_id, int):
        raise ValueError("podcast_id must be an integer")

    if not episode.get("published_parsed"):
        raise ValueError("Episode missing published date")

    published_at = datetime(*episode.published_parsed[:6])
    title = episode.get("title", "").strip()

    logger.debug(
        "Parsing episode podcast_id=%s title=%s published_at=%s",
        podcast_id,
        title,
        published_at,
    )

    return ValidatedEpisode(
        podcast_id=podcast_id,
        title=title,
        audio_link=get_audio_link_from_entry(episode),
        published_at=published_at,
        summary=episode.get("summary"),
    )


def transform_episodes_for_podcast(
    podcast_episode_data: dict,
) -> list[ValidatedEpisode]:
    """Convert a list of RSS entries into validated ValidatedEpisode models."""

    podcast_id = podcast_episode_data.get("podcast_id")
    podcast_title = podcast_episode_data.get("podcast_title", "unknown")
    raw_episodes = podcast_episode_data.get("new_episodes", [])

    logger.info(
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
            logger.exception(
                "Failed to parse episode for podcast id=%s title=%s",
                podcast_id,
                podcast_title,
            )
            continue

    logger.info(
        "Transformed episodes for podcast id=%s title=%s successful=%d failed=%d",
        podcast_id,
        podcast_title,
        len(transformed_episodes),
        len(raw_episodes) - len(transformed_episodes),
    )
    return transformed_episodes


def transform_all_podcast_episodes(podcast_episode_entries: list[dict]) -> list[dict]:
    """Transform the episode entries for all podcasts."""

    logger.info(
        "Starting transform for %d podcasts",
        len(podcast_episode_entries),
    )

    transformed_all = []
    for podcast_data in podcast_episode_entries:
        try:
            transformed_episodes = transform_episodes_for_podcast(podcast_data)
            transformed_data = {
                "podcast_id": podcast_data.get("podcast_id"),
                "podcast_title": podcast_data.get("podcast_title"),
                "new_episodes": transformed_episodes,
            }
            transformed_all.append(transformed_data)
        except Exception:
            logger.exception(
                "Failed to transform episodes for podcast title=%s",
                podcast_data.get("podcast_title", "unknown"),
            )

    total_transformed = sum(len(p.get("new_episodes", [])) for p in transformed_all)
    logger.info(
        "Transform complete. Processed podcasts=%d total_episodes=%d",
        len(podcast_episode_entries),
        total_transformed,
    )
    return transformed_all
