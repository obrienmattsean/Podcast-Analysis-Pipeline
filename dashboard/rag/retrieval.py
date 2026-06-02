"""Database retrieval operations for RAG pipeline.

Handles querying PostgreSQL for semantically similar podcast chunks
based on embedding similarity.
"""

import logging
import os

from psycopg2 import connect
from psycopg2.extensions import connection

logger = logging.getLogger(__name__)


def get_db_connection() -> connection:
    """Create a PostgreSQL database connection.

    Connects to RDS PostgreSQL instance using credentials from environment variables.

    Returns:
        An active psycopg2 connection object.
    """

    RDS_HOST = os.getenv("RDS_HOST")
    RDS_DB_NAME = os.getenv("RDS_DBNAME")
    RDS_USERNAME = os.getenv("RDS_USER")
    RDS_PASSWORD = os.getenv("RDS_PASSWORD")
    RDS_PORT = int(os.getenv("RDS_PORT", 5432))

    logger.info("Connecting to database: %s:%s/%s", RDS_HOST, RDS_PORT, RDS_DB_NAME)

    conn = connect(
        host=RDS_HOST, database=RDS_DB_NAME, user=RDS_USERNAME, password=RDS_PASSWORD, port=RDS_PORT
    )

    logger.info("Database connection established")
    return conn


def query_similar_chunks(
    conn: connection,
    embedding: list[float],
    top_k: int = 10,
    similarity_threshold: float = 0.5,
) -> list[dict]:
    """Query the database for the most similar chunks based on cosine similarity.

    Args:
        conn: Active PostgreSQL database connection.
        embedding: The query embedding vector as a list of floats.
        top_k: The number of top similar chunks to retrieve (default is 10).
        similarity_threshold: Minimum similarity score to include (default is 0.5).
            Results below this threshold are filtered out.

    Returns:
        A list of dictionaries containing the most similar chunks with keys:
            - episode_title: The title of the episode the chunk belongs to.
            - podcast_title: The title of the podcast the episode belongs to.
            - chunk_index: The index of the chunk within the episode.
            - chunk_transcript: The text content of the chunk.
            - similarity: The cosine similarity score between the query and chunk embeddings.

    Note:
        Results are always filtered by similarity_threshold before returning,
        so the output list may contain fewer than top_k items.
    """
    with conn.cursor() as cur:
        # Retrieve top-k chunk candidates by vector similarity.
        params: list[object] = [embedding, embedding]

        sql = """
        SELECT
            e.title,
            p.title,
            chunk_index,
            chunk_transcript,
            1 - (ec.embedding <=> %s::vector) AS similarity
        FROM episode_chunks ec
        JOIN episodes e ON ec.episode_id = e.id
        JOIN podcasts p ON e.podcast_id = p.id
        ORDER BY ec.embedding <=> %s::vector
        LIMIT %s
        """
        params.append(top_k)
        cur.execute(sql, params)
        results = cur.fetchall()

    similar_chunks = []
    for row in results:
        similarity = row[4]
        # Filter by similarity threshold
        if similarity >= similarity_threshold:
            similar_chunks.append(
                {
                    "episode_title": row[0],
                    "podcast_title": row[1],
                    "chunk_index": row[2],
                    "chunk_transcript": row[3],
                    "similarity": similarity,
                }
            )

    logger.info(
        "Retrieved %d chunks (threshold: %.2f, top_k: %d)",
        len(similar_chunks),
        similarity_threshold,
        top_k,
    )
    if similar_chunks:
        min_sim = min(c["similarity"] for c in similar_chunks)
        max_sim = max(c["similarity"] for c in similar_chunks)
        logger.info("Similarity range: %.2f - %.2f", min_sim, max_sim)

    return similar_chunks
