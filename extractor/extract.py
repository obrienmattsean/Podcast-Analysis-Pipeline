"""Extract podcasts from the database and fetch episodes from RSS feeds."""

import logging
from datetime import datetime
from pprint import pprint

import feedparser
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def insert_podcast(conn: connection, rss_url: str) -> None:
    """Insert a new podcast into the database with the given RSS URL.

    Args:
        conn (connection): Active psycopg2 database connection.
        rss_url (str): The RSS feed URL of the podcast to insert.

    Returns:
        None

    Raises:
        ValueError: If rss_url is not a non-empty string.
        Exception: If database insertion fails.
    """

    if not isinstance(rss_url, str) or not rss_url:
        raise ValueError("RSS URL must be a non-empty string.")

    parts = rss_url.split("/")
    title = parts[-2] if len(parts) > 1 else "unknown"

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO podcasts (rss_url, title) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (rss_url, title),
            )
            conn.commit()
            logger.info("Inserted podcast with RSS URL: %s and title: %s", rss_url, title)
    except Exception:
        conn.rollback()
        logger.exception("Failed to insert podcast with RSS URL: %s", rss_url)
        raise


def get_podcasts_from_database(conn: connection) -> list[dict]:
    """Fetch podcast metadata rows from the database.

    Args:
        conn (connection): Active psycopg2 database connection.

    Returns:
        list: Podcast rows containing id, title, and rss_url.
    """

    logger.info("Fetching podcasts from database")
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT id, title, rss_url FROM podcasts")
        podcasts = cursor.fetchall()

    logger.info("Fetched %d podcasts from database", len(podcasts))
    return podcasts


def get_latest_episode_date_from_podcast(conn: connection, podcast_id: int) -> datetime | None:
    """Fetch the most recent episode publication date for a podcast.

    Args:
        conn (connection): Active psycopg2 database connection.
        podcast_id (int): Podcast identifier.

    Returns:
        datetime | None: Latest publication datetime, or None if no rows exist.

    Raises:
        ValueError: If podcast_id is not an integer.
    """

    if not isinstance(podcast_id, int):
        raise ValueError("Podcast ID must be a non-empty integer.")

    logger.debug("Querying latest episode date for podcast_id=%s", podcast_id)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT pub_date
            FROM episodes
            WHERE podcast_id = %s
            ORDER BY pub_date
            DESC LIMIT 1""",
            (podcast_id,),
        )
        result = cursor.fetchone()
    logger.debug(
        "Latest episode date query complete for podcast_id=%s",
        podcast_id,
    )
    return result["pub_date"] if result else None


def get_episodes_from_rss(url: str) -> list:
    """Fetch and parse RSS entries for a podcast feed URL.

    Args:
        url (str): RSS feed URL.

    Returns:
        list: Parsed feed entries.

    Raises:
        ValueError: If url is not a non-empty string.
    """

    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a non-empty string.")

    logger.info("Fetching episodes from RSS feed: %s", url)
    feed = feedparser.parse(url)
    logger.info("Fetched %d episodes from RSS feed", len(feed.entries))
    return feed.entries


def filter_episodes_by_datetime(
    episodes: list[dict], cutoff_datetime: datetime = None
) -> list[dict]:
    """Filter episodes to only include those published after a cutoff date.

    Args:
        episodes (list[dict]): List of episode entries with 'published_parsed' field.
        cutoff_datetime (datetime | None): Datetime to filter episodes against.

    Returns:
        list[dict]: Filtered list of episodes published after the cutoff date.
    """

    new_episodes = []
    for episode in episodes:
        try:
            published_at = datetime(*episode["published_parsed"][:6])
        except Exception:
            logger.warning("Skipping episode with invalid published date")
            continue

        if not cutoff_datetime:
            if len(new_episodes) < 15:
                new_episodes.append(episode)
            else:
                break
        elif published_at > cutoff_datetime:
            new_episodes.append(episode)
        else:
            continue
    return new_episodes


def get_new_episodes_for_podcast(conn: connection, podcast: dict) -> list[dict]:
    """Get new RSS episodes for a single podcast compared with DB state.

    Args:
        conn (connection): Active psycopg2 database connection.
        podcast (dict): Podcast metadata containing id, title, and rss_url.

    Returns:
        list[dict]: RSS entries that are newer than the latest stored episode.
    """

    podcast_id = podcast["id"]
    podcast_title = podcast.get("title", "unknown")
    logger.info("Checking podcast id=%s title=%s", podcast_id, podcast_title)

    latest_episode_date = get_latest_episode_date_from_podcast(conn, podcast["id"])
    if latest_episode_date:
        logger.debug(
            "Latest stored episode date for podcast_id=%s is %s",
            podcast_id,
            latest_episode_date,
        )
    else:
        logger.info(
            "No existing episodes found for podcast_id=%s. Will collect up to 15 episodes",
            podcast_id,
        )

    episodes = get_episodes_from_rss(podcast["rss_url"])
    filtered_episodes = filter_episodes_by_datetime(episodes, cutoff_datetime=latest_episode_date)

    logger.info(
        "Podcast id=%s title=%s has %d new episodes",
        podcast_id,
        podcast_title,
        len(filtered_episodes),
    )
    return filtered_episodes


def extract_new_episodes(conn: connection) -> list[dict]:
    """Extract new episodes for all podcasts in the database

    This is the main orchestration function that:
    1. Fetches all podcasts from the database
    2. For each podcast, extracts new episodes from its RSS feed that aren't already in the database
    3. Returns all episodes with their associated podcast information

    Args:
        conn: PostgreSQL database connection object

    Returns:
        list: List of dictionaries with structure:
              {
                  'podcast_id': int,
                  'podcast_name': str,
                  'episodes': list[dict]
              }
              Each episode dict contains all RSS fields like:
              title, published, published_parsed, links, summary, etc.
    """

    logger.info("Starting new episode extraction")
    podcasts = get_podcasts_from_database(conn)
    extracted_episodes = []
    for podcast in podcasts:
        try:
            new_episodes = get_new_episodes_for_podcast(conn, podcast)
            if not new_episodes:
                logger.info(
                    "No new episodes found for podcast id=%s title=%s",
                    podcast["id"],
                    podcast.get("title", "unknown"),
                )
                continue
            podcast_episode_data = {
                "podcast_id": podcast["id"],
                "podcast_title": podcast.get("title", "unknown"),
                "new_episodes": new_episodes,
            }
            extracted_episodes.append(podcast_episode_data)
        except Exception:
            logger.exception(
                "Failed to extract episodes for podcast title=%s id=%s",
                podcast.get("title"),
                podcast.get("id"),
            )

    total_new_episodes = sum(
        len(episode_data["new_episodes"]) for episode_data in extracted_episodes
    )
    logger.info(
        "Extraction complete. Processed podcasts=%d, total_new_episodes=%d",
        len(podcasts),
        total_new_episodes,
    )
    return extracted_episodes


if __name__ == "__main__":
    # Run locally for testing
    url = "https://media.rss.com/peopleofculture/feed.xml"
    a = get_episodes_from_rss(url)
    pprint(a)
