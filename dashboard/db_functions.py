"""Database utility functions for the dashboard."""

import os

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


def get_all_podcast_titles(conn: connection) -> list[dict]:
    """Fetches all podcasts from the database."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT title FROM podcasts;")
        rows = cursor.fetchall()
        return [row[0] for row in rows]


if __name__ == "__main__":
    conn = get_db_connection()
    print("Database connection established successfully.")
    podcasts = get_all_podcast_titles(conn)
    print("Sample podcasts:", podcasts[:5])
    conn.close()
