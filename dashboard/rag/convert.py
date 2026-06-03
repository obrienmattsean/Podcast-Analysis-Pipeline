"""Query embedding conversion for RAG pipeline.

Handles converting user queries into embedding vectors using OpenAI's
embedding model for semantic similarity search.
"""

import logging
import os

from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536


def get_openai_client() -> OpenAI:
    """Get an OpenAI client instance.

    Creates a client configured with the API key from environment variables.

    Returns:
        An initialized OpenAI client.

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def get_query_embedding(client: OpenAI, text: str) -> list[float]:
    """Get embedding vector for user's question using OpenAI.

    Args:
        client: Initialized OpenAI client.
        text: The text to embed (user query).

    Returns:
        List of floats representing the embedding vector.

    Raises:
        OpenAIError: If the API request fails.
    """

    try:
        response = client.embeddings.create(
            model=MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSION,
        )
        return response.data[0].embedding
    except OpenAIError as e:
        logger.error("Error occurred when generating query embedding: %s", str(e))
        raise
