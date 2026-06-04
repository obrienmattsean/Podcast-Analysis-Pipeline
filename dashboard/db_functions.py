"""Database utility functions for the dashboard."""

import json
import os
from datetime import datetime

import boto3
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import connection

load_dotenv()


def get_db_connection() -> connection:
    """Establish a connection to the PostgreSQL database using environment variables.

    Returns:
        connection: An open psycopg2 connection to the configured PostgreSQL database.
    """
    return connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DBNAME"),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        port=5432,
    )


def get_all_podcasts(conn: connection) -> list[dict]:
    """Fetch all podcasts from the database.

    Args:
        conn: An open psycopg2 database connection.

    Returns:
        list[dict]: List of podcast dicts, each containing ``podcast_title``, ``num_episodes``,
            ``avg_sentiment_score``, ``tracked_since``, and ``last_updated``.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.title AS podcast_title,
            COUNT(e.episode_id) AS num_episodes,
            ROUND(AVG(e.sentiment_score)::numeric, 2) AS avg_sentiment_score,
            MIN(e.pub_date) AS tracked_since,
            MAX(e.pub_date) AS last_updated,
            p.podcast_id
            FROM podcasts p
            LEFT JOIN episodes e USING (podcast_id)
            GROUP BY p.podcast_id
            ORDER BY last_updated DESC NULLS LAST;
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "podcast_title": row[0],
                "num_episodes": row[1],
                "avg_sentiment_score": row[2],
                "tracked_since": row[3],
                "last_updated": row[4],
                "podcast_id": row[5],
            }
            for row in rows
        ]


def trigger_pipeline(rss_url: str) -> str:
    """Start the podcast pipeline Step Function execution for a given RSS feed.

    Args:
        rss_url: The RSS feed URL to pass as pipeline input.

    Returns:
        str: The ARN of the started Step Function execution.

    Raises:
        EnvironmentError: If ``STEP_FUNCTION_ARN`` is not set.
    """
    state_machine_arn = os.getenv("STEP_FUNCTION_ARN")
    if not state_machine_arn:
        raise OSError("STEP_FUNCTION_ARN environment variable is not set.")
    region = os.getenv("AWS_REGION", "eu-west-2")
    client = boto3.client("stepfunctions", region_name=region)
    response = client.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps({"rss_url": rss_url}),
    )
    return response["executionArn"]


def _hours_elapsed(dt: datetime) -> int:
    return int((datetime.now() - dt).total_seconds() // 3600)


def format_last_updated(last_updated: datetime | None) -> str:
    """Format the most recent episode date as a compact relative string.

    Args:
        last_updated: The publication date of the most recent tracked episode,
            or None if no episodes have been tracked.

    Returns:
        str: A compact relative string such as ``"2h ago"``, ``"yesterday"``,
            ``"3d ago"``, or ``"never"``.

    Example:
        >>> from datetime import datetime, timedelta
        >>> format_last_updated(datetime.now() - timedelta(hours=3))
        '3h ago'
    """
    if last_updated is None:
        return "never"
    hours = _hours_elapsed(last_updated)
    if hours < 24:
        return f"{hours}h ago"
    if hours < 48:
        return "yesterday"
    days = hours // 24
    return f"{days}d ago"


def format_tracked_since(tracked_since: datetime | None) -> str:
    """Format the tracked_since date as a human-readable string.

    Args:
        tracked_since: The earliest episode publication date, or None if no
            episodes have been tracked yet.

    Returns:
        str: A formatted date string like ``"January 15, 2024"`` or ``"N/A"``.

    Example:
        >>> from datetime import datetime
        >>> format_tracked_since(datetime(2024, 1, 15))
        'January 15, 2024'
    """
    if tracked_since is None:
        return "N/A"
    return tracked_since.strftime("%B %d, %Y")


def format_time_since_published(pub_date: datetime) -> str:
    """Format the time since an episode was published as a human-readable string.

    Args:
        pub_date: The publication date of the episode.

    Returns:
        str: A human-readable string such as ``"5 hours ago"``,
            ``"Yesterday"``, or ``"3 days ago"``.

    Example:
        >>> from datetime import datetime, timedelta
        >>> format_time_since_published(datetime.now() - timedelta(hours=5))
        '5 hours ago'
    """
    hours = _hours_elapsed(pub_date)
    if hours < 24:
        return f"{hours} hour ago" if hours == 1 else f"{hours} hours ago"
    if hours < 48:
        return "Yesterday"
    days = hours // 24
    return f"{days} days ago"


def get_recent_episodes(conn: connection, limit: int = 10) -> list[dict]:
    """Fetch the most recent episodes from the database.

    Args:
        conn: An open psycopg2 database connection.
        limit: Maximum number of episodes to return. Defaults to 10.

    Returns:
        list[dict]: List of episode dicts, each containing ``podcast_title``,
            ``episode_title``, ``time_since_published``, ``summary``,
            ``sentiment_score``, ``flagged``, and ``keywords``.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.title AS podcast_title,
            e.title AS episode_title,
            e.pub_date,
            e.summary,
            e.sentiment_score,
            e.flagged,
            COALESCE(
                ARRAY_AGG(ent.name ORDER BY ent.name) FILTER (WHERE ent.name IS NOT NULL),
                ARRAY[]::text[]
            ) AS keywords
            FROM episodes e
            JOIN podcasts p USING (podcast_id)
            LEFT JOIN episode_entities ee USING (episode_id)
            LEFT JOIN entities ent ON ee.entity_id = ent.entity_id AND ent.entity_type = 'topic'
            GROUP BY e.episode_id, p.title, e.title, e.pub_date,
                e.summary, e.sentiment_score, e.flagged
            ORDER BY e.pub_date DESC
            LIMIT %s;
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            {
                "podcast_title": row[0],
                "episode_title": row[1],
                "time_since_published": format_time_since_published(row[2]),
                "summary": row[3],
                "sentiment_score": row[4],
                "flagged": row[5],
                "keywords": row[6],
            }
            for row in rows
        ]


def get_keywords_for_episode(conn: connection, episode_id: int) -> list[str]:
    """Fetch the top keywords for a given episode.

    Args:
        conn: An open psycopg2 database connection.
        episode_id: The ID of the episode to fetch keywords for.
    Returns:
        list[str]: A list of keyword strings associated with the episode.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT entities.name
            FROM episode_entities
            JOIN entities USING (entity_id)
            WHERE episode_id = %s AND entity_type = 'topic';
            """,
            (episode_id,),
        )
        rows = cursor.fetchall()
        return [row[0] for row in rows]


def get_keywords_for_podcast(conn: connection, podcast_id: int) -> list[str]:
    """Fetch the top keywords for a given podcast.

    Args:
        conn: An open psycopg2 database connection.
        podcast_id: The ID of the podcast to fetch keywords for.
    Returns:
        list[str]: A list of keyword strings associated with the podcast.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT entities.name, count(*) AS mention_count
            FROM podcasts
            JOIN episodes USING (podcast_id)
            JOIN episode_entities USING (episode_id)
            JOIN entities USING (entity_id)
            WHERE podcast_id = %s AND entity_type = 'topic'
            GROUP BY entities.name
            ORDER BY mention_count DESC;
            """,
            (podcast_id,),
        )
        rows = cursor.fetchall()

        return list(rows)
