"""Text chunking and embedding transformation for RAG pipeline."""

import logging
import os
from pprint import pprint

import tiktoken
from dotenv import load_dotenv
from openai import APIError, OpenAI, OpenAIError, RateLimitError

load_dotenv()

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 256


def get_openai_client():
    """Get OpenAI client instance."""
    return OpenAI(api_key=OPENAI_API_KEY)


def get_tokenizer(model: str = EMBEDDING_MODEL):
    """Get tiktoken tokenizer for the embedding model."""
    encoding = tiktoken.encoding_for_model(model)
    return encoding


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
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


def embed_text(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    """Get embedding vector for the given text."""
    client = get_openai_client()
    try:
        response = client.embeddings.create(input=text, model=model)
        embedding = response.data[0].embedding
        return embedding
    except (OpenAIError, APIError, RateLimitError) as e:
        logger.error("Failed to get embedding: %s", e)
        raise


def embed_chunks(
    chunks: list[dict[str, str]], model: str = EMBEDDING_MODEL
) -> list[dict[str, any]]:
    """Embed a list of text chunks."""
    embedded_chunks = []
    for chunk in chunks:
        try:
            embedding = embed_text(chunk["text"], model)
            embedded_chunk = {
                "chunk_index": chunk["chunk_index"],
                "embedding": embedding,
                "text": chunk["text"],
            }
            embedded_chunks.append(embedded_chunk)
        except (OpenAIError, APIError, RateLimitError) as e:
            logger.error("Failed to embed chunk %d: %s", chunk["chunk_index"], e)
        except Exception as e:
            logger.error("Unexpected error embedding chunk %d: %s", chunk["chunk_index"], e)
    logger.info("Successfully embedded %d/%d chunks", len(embedded_chunks), len(chunks))
    return embedded_chunks


def process_transcript(transcript: str) -> list[dict[str, any]]:
    """Process transcript text into embedded chunks."""
    logger.info("Transforming transcript")
    chunks = chunk_text(transcript)
    embedded_chunks = embed_chunks(chunks)
    logger.info("Transformation complete: %s embedded chunks", len(embedded_chunks))
    return embedded_chunks


if __name__ == "__main__":
    # Example usage
    with open("./tmp/transcript.txt") as f:
        text = f.read()

    embedded_chunks = process_transcript(text)
    pprint(embedded_chunks[0])  # Print first embedded chunk for verification
    print(f"Processed {len(embedded_chunks)} embedded chunks")
