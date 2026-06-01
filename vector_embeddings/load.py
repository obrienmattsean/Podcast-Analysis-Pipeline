"""Load vector embeddings into PostgreSQL database.

This module handles database operations for storing episode chunks
and their corresponding embedding vectors for RAG pipeline retrieval.
"""

import json
import logging
import os

import boto3
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)


def get_secrets() -> dict:
    client = boto3.client("secretsmanager")

    resp = client.get_secret_value(SecretId=os.environ["SECRETS_ARN"])

    return json.loads(resp["SecretString"])


def get_db_connection() -> connection:
    """Create a PostgreSQL connection from environment configuration.

    Returns:
        connection: Active psycopg2 database connection.

    Raises:
        Exception: Raised when the database connection fails.
    """

    try:
        secrets = get_secrets()

        return connect(
            host=secrets["RDS_HOST"],
            database=secrets["RDS_DBNAME"],
            user=secrets["RDS_USER"],
            password=secrets["RDS_PASSWORD"],
            port=5432,
            sslmode="require",
        )
    except Exception:
        logging.exception("Failed to connect to database")
        raise


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
