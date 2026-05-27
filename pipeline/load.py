"""Python module to load the extracted data into the database."""

import logging
import os

from model import ValidatedEpisode
from psycopg2 import connect
from psycopg2.extensions import connection


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


def insert_episode_into_database(conn, episode: ValidatedEpisode) -> None:
    """Insert a single ValidatedEpisode row using an existing connection."""

    with conn.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO episodes (
            podcast_id, title, audio_url, published_at, transcribed
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
            (
                episode.podcast_id,
                episode.title,
                str(episode.audio_link),
                episode.published_at,
                episode.transcribed,
            ),
        )


def insert_podcast_episodes(
    conn: connection, podcast_episode_data: dict
) -> tuple[int, int]:
    """Insert episodes for one podcast and return (inserted, failed)."""

    podcast_title = podcast_episode_data.get("podcast_title", "unknown")
    podcast_id = podcast_episode_data.get("podcast_id")
    episodes = podcast_episode_data.get("new_episodes", [])

    logger.info(
        "Loading episodes for podcast title=%s id=%s count=%d",
        podcast_title,
        podcast_id,
        len(episodes),
    )

    inserted_count = 0
    failed_count = 0

    for episode in episodes:
        try:
            insert_episode_into_database(conn, episode)
            inserted_count += 1
        except Exception:
            failed_count += 1
            logger.exception(
                "Failed to insert episode title=%s podcast=%s",
                getattr(episode, "title", "unknown"),
                podcast_title,
            )

    if failed_count:
        conn.rollback()
        logger.warning(
            "Rolled back podcast batch due to insert failures. "
            "podcast=%s inserted=%d failed=%d",
            podcast_title,
            inserted_count,
            failed_count,
        )
        return 0, failed_count

    conn.commit()
    logger.info(
        "Podcast load complete title=%s id=%s inserted=%d",
        podcast_title,
        podcast_id,
        inserted_count,
    )
    return inserted_count, failed_count


def insert_all_episodes(conn: connection, enteries: list[dict]) -> None:
    """Inserts all new episodes into the database."""

    logger.info("Starting episode load for %d podcasts", len(enteries))
    total_inserted = 0
    total_failed = 0

    for podcast_episode_data in enteries:
        inserted_count, failed_count = insert_podcast_episodes(
            conn,
            podcast_episode_data,
        )
        total_inserted += inserted_count
        total_failed += failed_count

    logger.info(
        "Episode load complete. total_inserted=%d total_failed=%d",
        total_inserted,
        total_failed,
    )
