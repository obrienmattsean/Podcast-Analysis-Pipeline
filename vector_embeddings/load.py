"""Load vector embeddings into PostgreSQL database.

This module handles database operations for storing episode chunks
and their corresponding embedding vectors for RAG pipeline retrieval.
"""

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
    """Create a PostgreSQL database connection.

    Connects to RDS PostgreSQL instance using credentials from environment variables.

    Returns:
        An active psycopg2 connection object.
    """
    logger.info("Connecting to database: %s:%s/%s", RDS_HOST, RDS_PORT, RDS_DB_NAME)

    conn = psycopg2.connect(
        host=RDS_HOST, database=RDS_DB_NAME, user=RDS_USERNAME, password=RDS_PASSWORD, port=RDS_PORT
    )

    logger.info("Database connection established")
    return conn


def insert_embeddings(conn: connection, episode_id: int, chunks: list[dict]) -> None:
    """Insert episode chunks and their embedding vectors into the database.

    Args:
        conn: Active PostgreSQL database connection.
        episode_id: The ID of the episode being processed.
        chunks: List of chunk dictionaries with keys:
            - chunk_index: Integer index of the chunk.
            - text: Text content of the chunk.
            - embedding: List of floats representing the embedding vector.

    Raises:
        Exception: If database insertion fails. Connection is rolled back on error.

    Example:
        >>> chunks = [
        ...     {
        ...         "chunk_index": 0,
        ...         "text": "Introduction text...",
        ...         "embedding": [0.1, 0.2, ...]
        ...     }
        ... ]
        >>> insert_embeddings(conn, 199, chunks)
    """
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
