"""Extract podcasts from the database and fetch episodes from RSS feeds."""

import logging
import os
from datetime import datetime

import feedparser
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


def get_database_connection() -> connection:
  """Create a PostgreSQL connection from environment configuration.

  Returns:
      connection: Active psycopg2 database connection.

  Raises:
      Exception: Raised when the database connection fails.
  """

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


def insert_podcast(rss_url: str) -> None:
  """Insert a new podcast into the database with the given RSS URL.

  Args:
      rss_url (str): The RSS feed URL of the podcast to insert.

  Returns:
      None

  Raises:
      ValueError: If rss_url is not a non-empty string.
      Exception: If database insertion fails.
  """

  if not isinstance(rss_url, str) or not rss_url:
    raise ValueError("RSS URL must be a non-empty string.")

  conn = get_database_connection()
  try:
    with conn.cursor() as cursor:
      cursor.execute(
        "INSERT INTO podcasts (rss_url) VALUES (%s) ON CONFLICT DO NOTHING",
        (rss_url,),
      )
      conn.commit()
      logger.info("Inserted podcast with RSS URL: %s", rss_url)
  except Exception:
    logger.exception("Failed to insert podcast with RSS URL: %s", rss_url)
    raise
  finally:
    conn.close()


def get_podcasts_from_database(conn: connection) -> list:
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
      Optional[datetime]: Latest publication datetime, or None if no rows exist.

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
      "No existing episodes found for podcast_id=%s. Will collect up to 15 episodes",
      podcast_id,
    )

  episodes = get_episodes_from_rss(podcast["rss_url"])
  new_episodes = []
  for episode in episodes:
    try:
      published_at = datetime(*episode["published_parsed"][:6])
    except Exception:
      logger.warning(
        "Skipping episode with invalid published date for podcast_id=%s title=%s",
        podcast_id,
        podcast_title,
      )
      continue

    if not latest_episode_date:
      if len(new_episodes) < 15:
        new_episodes.append(episode)
      else:
        break
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

  total_new_episodes = sum(len(episode_data["new_episodes"]) for episode_data in extracted_episodes)
  logger.info(
    "Extraction complete. Processed podcasts=%d, total_new_episodes=%d",
    len(podcasts),
    total_new_episodes,
  )
  return extracted_episodes
