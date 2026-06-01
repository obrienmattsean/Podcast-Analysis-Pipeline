"""Text chunking and embedding transformation for RAG pipeline.

Handles splitting long transcripts into overlapping chunks and generating
vector embeddings using OpenAI's embedding model for semantic search retrieval.
"""

import logging
import os

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
BATCH_SIZE = 20


def get_openai_client() -> OpenAI:
    """Get an OpenAI client instance.

    Creates a client configured with the API key from environment variables.

    Returns:
        An initialized OpenAI client.

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not set")

    return OpenAI(api_key=OPENAI_API_KEY)


def get_tokenizer(model: str = EMBEDDING_MODEL) -> tiktoken.Encoding:
    """Get tiktoken tokenizer for the specified embedding model.

    Args:
        model: Name of the embedding model (defaults to text-embedding-3-small).

    Returns:
        A tiktoken encoding instance for the model.
    """
    return tiktoken.encoding_for_model(model)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Split text into overlapping chunks using token-based boundaries.

    Args:
        text: The input text to chunk.
        chunk_size: Maximum number of tokens per chunk (defaults to 800).
        overlap: Number of tokens to overlap between consecutive chunks (defaults to 100).

    Returns:
        List of chunk dictionaries with keys:
            - text: The chunk text content.
            - chunk_index: Zero-based index of the chunk.
    """
    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0
    chunk_index = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunk = {"text": chunk_text, "chunk_index": chunk_index}
        chunks.append(chunk)
        start += chunk_size - overlap  # Move start forward with overlap
        chunk_index += 1
    return chunks


def embed_text_batch(
    client: OpenAI, batch: list[str], model: str = EMBEDDING_MODEL
) -> list[list[float]]:
    """Generate embedding vectors for a batch of texts using OpenAI API.

    Args:
        client: The OpenAI client instance to use for API requests.
        batch: The list of input texts to embed.
        model: The embedding model to use (defaults to text-embedding-3-small).

    Returns:
        List of embedding vectors, each as a list of floats.

    Raises:
        OpenAIError: If the API request fails.
    """
    try:
        response = client.embeddings.create(input=batch, model=model)
        embeddings = [embedding.embedding for embedding in response.data]
        return embeddings
    except OpenAIError as e:
        logger.error("Failed to get embeddings for batch: %s", e)
        raise


def embed_chunks(client: OpenAI, chunks: list[dict], model: str = EMBEDDING_MODEL) -> list[dict]:
    """Generate embeddings for a list of text chunks.

    Processes chunks in batches for efficiency, handling errors gracefully.
    Failed batches are logged but do not halt processing.

    Args:
        client: The OpenAI client instance to use for API requests.
        chunks: List of chunk dictionaries with keys:
            - text: The chunk text content.
            - chunk_index: Index of the chunk.
        model: The embedding model to use (defaults to text-embedding-3-small).

    Returns:
        List of embedded chunk dictionaries with keys:
            - chunk_index: Index of the chunk.
            - embedding: List of floats representing the embedding vector.
            - text: The original chunk text.

    Note:
        Chunks from failed batches are skipped, so the output list may be shorter
        than the input list.
    """
    embedded_chunks = []

    for i in range(0, len(chunks), BATCH_SIZE):
        batch_chunks = chunks[i : i + BATCH_SIZE]
        batch_texts = [chunk["text"] for chunk in batch_chunks]

        try:
            embeddings = embed_text_batch(client, batch_texts, model)
            for j, chunk in enumerate(batch_chunks):
                embedded_chunk = {
                    "chunk_index": chunk["chunk_index"],
                    "embedding": embeddings[j],
                    "text": chunk["text"],
                }
                embedded_chunks.append(embedded_chunk)
        except OpenAIError as e:
            logger.error(
                "Embedding failed for batch starting at chunk_index %d: %s",
                batch_chunks[0]["chunk_index"],
                e,
            )
            continue  # Skip this batch and proceed with the next
    logger.info("Successfully embedded %d/%d chunks", len(embedded_chunks), len(chunks))
    return embedded_chunks


def process_transcript(client: OpenAI, transcript: str) -> list[dict]:
    """Process transcript into chunks and generate their embeddings.

    Orchestrates the full transformation pipeline:
    1. Splits transcript into overlapping token-based chunks
    2. Generates embedding vectors for each chunk via OpenAI API

    Args:
        client: The OpenAI client instance to use for API requests.
        transcript: The full transcript text to process.

    Returns:
        List of embedded chunk dictionaries with keys:
            - chunk_index: Position of the chunk in the transcript.
            - embedding: The embedding vector as a list of floats.
            - text: The chunk text content.

    """
    logger.info(
        "Transforming transcript into %d-token chunks with %d-token overlap",
        CHUNK_SIZE,
        CHUNK_OVERLAP,
    )
    chunks = chunk_text(transcript)

    logger.info("Created %d chunks from transcript", len(chunks))
    embedded_chunks = embed_chunks(client, chunks)

    logger.info("Transformation complete: %d embedded chunks", len(embedded_chunks))
    return embedded_chunks
