"""Database utility functions for the dashboard."""

import os
from datetime import datetime

from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import connection

load_dotenv()


def get_db_connection() -> connection:
    """Establish a connection to the PostgreSQL database using environment variables."""
    return connect(
        host=os.getenv("RDS_HOST"),
        database=os.getenv("RDS_DBNAME"),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        port=5432,
    )


def get_days_since_published(pub_date: datetime) -> int:
    """Calculate the number of days since the episode was published."""
    today = datetime.today()
    return (today - pub_date).days


def get_recent_episodes(conn: connection, limit: int = 10) -> list[dict]:
    """Fetches the most recent episodes from the database."""
    with conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.title, p.title AS podcast_title, e.pub_date
            FROM episodes e
            JOIN podcasts p ON e.podcast_id = p.id
            ORDER BY e.pub_date DESC
            LIMIT %s;
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return [
            {
                "title": row[0],
                "podcast_title": row[1],
                "days_since_published": get_days_since_published(row[2]),
                "link"
            }
            for row in rows
        ]


if __name__ == "__main__":
    conn = get_db_connection()
    print("Database connection established successfully.")
    recent_episodes = get_recent_episodes(conn)
    print("Sample recent episodes:", recent_episodes[:5])
    conn.close()
