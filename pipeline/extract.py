"""Extract podcasts from the database and fetch episodes from RSS feeds."""

import logging
import os
from datetime import datetime

import feedparser
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


def get_logger() -> None:
    """Configures application logging."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )
    return logging.getLogger(__name__)


logger = get_logger()


def get_database_connection() -> connection:
    """Establishes a connection to the PostgreSQL database using environment variables."""

    try:
        logger.info(
            "Connecting to PostgreSQL database at host: %s",
            os.getenv("RDS_HOST"),
        )
        conn = connect(
            host=os.getenv("RDS_HOST"),
            database=os.getenv("RDS_DB_NAME"),
            user=os.getenv("RDS_USERNAME"),
            password=os.getenv("RDS_PASSWORD"),
        )
        logger.info("Database connection established")
        return conn
    except Exception:
        logger.exception("Failed to connect to the database")
        raise


def get_podcasts_from_database(conn: connection) -> list:
    """Fetches the podcasts from the database."""

    logger.info("Fetching podcasts from database")
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT id, title, rss_url FROM podcasts")
        podcasts = cursor.fetchall()

    logger.info("Fetched %d podcasts from database", len(podcasts))
    return podcasts


def get_latest_episode_date_from_podcast(conn: connection, podcast_id: str) -> datetime:
    """Fetches the latest episode date from the database for a given podcast ID."""

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
    """Fetches the episodes from the RSS feed."""

    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a non-empty string.")

    logger.info("Fetching episodes from RSS feed: %s", url)
    feed = feedparser.parse(url)
    logger.info("Fetched %d episodes from RSS feed", len(feed.entries))
    return feed.entries


def get_new_episodes_for_podcast(
    conn: connection,
    podcast: dict,
) -> list[dict]:
    """Fetches the new episodes for a given podcast."""

    podcast_id = podcast["id"]
    podcast_title = podcast.get("title", "unknown")
    logger.info("Checking podcast id=%s title=%s", podcast_id, podcast_title)

    latest_episode_date = get_latest_episode_date_from_podcast(
        conn,
        podcast["id"],
    )
    if latest_episode_date:
        logger.debug(
            "Latest stored episode date for podcast_id=%s is %s",
            podcast_id,
            latest_episode_date,
        )
    else:
        logger.info(
            "No existing episodes found for podcast_id=%s. "
            "Will collect up to 5 episodes",
            podcast_id,
        )

    episodes = get_episodes_from_rss(podcast["rss_url"])
    new_episodes = []
    for episode in episodes:
        try:
            published_at = datetime(*episode.published_parsed[:6])
        except Exception:
            logger.warning(
                "Skipping episode with invalid published date for podcast_id=%s title=%s",
                podcast_id,
                podcast_title,
            )
            continue

        if not latest_episode_date and len(new_episodes) < 5:
            new_episodes.append(episode)
        elif published_at > latest_episode_date:
            new_episodes.append(episode)
        else:
            continue

    logger.info(
        "Podcast id=%s title=%s has %d new episodes",
        podcast_id,
        podcast_title,
        len(new_episodes),
    )
    return new_episodes


def extract_new_episodes(conn: connection):
    """Extract new episodes for all podcasts in the database."""

    logger.info("Starting new episode extraction")
    podcasts = get_podcasts_from_database(conn)
    extracted_episodes = []
    for podcast in podcasts:
        try:
            new_episodes = get_new_episodes_for_podcast(conn, podcast)
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
    url = "https://media.rss.com/fluxcapacitor/feed.xml"
    curr = get_episodes_from_rss(url)[0]
