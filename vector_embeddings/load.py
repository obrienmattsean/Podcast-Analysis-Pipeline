"""Script to load vector embeddings into the database."""

import logging
import os

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

RDS_HOST = os.getenv("RDS_HOST")
RDS_DB_NAME = os.getenv("RDS_DBNAME")
RDS_USERNAME = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_PORT = int(os.getenv("RDS_PORT", 5432))


def get_db_connection() -> connection:
    """Create database connection."""
    logger.info("Connecting to database: %s:%s/%s", RDS_HOST, RDS_PORT, RDS_DB_NAME)

    conn = psycopg2.connect(
        host=RDS_HOST, database=RDS_DB_NAME, user=RDS_USERNAME, password=RDS_PASSWORD, port=RDS_PORT
    )

    logger.info("Database connection established")
    return conn


def insert_embeddings(conn: connection, episode_id: int, chunks: list[dict[str, any]]) -> None:
    """Insert embedding vectors into the database."""
    records = [
        (episode_id, chunk["chunk_index"], chunk["text"], chunk["embedding"]) for chunk in chunks
    ]
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                                INSERT INTO episode_chunks
                                (episode_id, chunk_index, chunk_transcript, embedding)
                                VALUES %s
                                """,
                records,
            )
            conn.commit()
            logger.info("Inserted %d embeddings for episode_id %d", len(chunks), episode_id)
    except Exception as e:
        logger.error("Failed to insert embeddings for episode_id %d: %s", episode_id, e)
        conn.rollback()
        raise
