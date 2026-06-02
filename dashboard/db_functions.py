"""Database utility functions for the dashboard."""

import os
from datetime import datetime

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


def get_days_since_published(pub_date: datetime) -> int:
    """Calculate the number of days since the episode was published.

    Args:
        pub_date: The publication date of the episode.

    Returns:
        int: Number of whole days elapsed since ``pub_date``.
    """
    today = datetime.today()
    return (today - pub_date).days


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
    hours = int((datetime.now() - pub_date).total_seconds() // 3600)
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
            ``episode_title``, ``days_since_published``, and
            ``time_since_published``.
    """
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.title AS podcast_title,
            e.title AS episode_title,
            e.pub_date,
            e.summary,
            e.sentiment_score
            FROM episodes e
            JOIN podcasts p USING (podcast_id)
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
            }
            for row in rows
        ]


if __name__ == "__main__":
    conn = get_db_connection()
    print("Database connection established successfully.")
    recent_episodes = get_recent_episodes(conn)
    print("Sample recent episodes:", recent_episodes[:5])
    conn.close()
