"""Response generation for RAG pipeline using retrieved context.

Generates LLM responses based on user queries and retrieved podcast chunks
using OpenAI's chat completion API.
"""

import logging

from convert import get_openai_client, get_query_embedding
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from retrieval import get_db_connection, query_similar_chunks

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a knowledgeable podcast assistant.
You answer questions based on the provided podcast transcripts.
Be concise, informative, and cite specific episodes or timestamps when relevant.
If the provided context doesn't contain relevant information, say so clearly.

- Do not answer questions that are not related to the podcast content.
- Do not make up information that is not present in the retrieved chunks.
- Always refer to the episode title and podcast title when citing information from the chunks.
- Use the similarity score to prioritize more relevant chunks in your answer.
"""


def build_context(retrieved_chunks: list[dict]) -> str:
    """Build context string from retrieved chunks for LLM input.

    Args:
        retrieved_chunks: List of dictionaries with retrieved chunk data.
            Each dict should contain keys:
            - episode_title: Title of the episode
            - podcast_title: Title of the podcast
            - chunk_transcript: Text content of the chunk
            - similarity: Cosine similarity score

    Returns:
        Formatted context string ready for LLM input.

    Example:
        >>> chunks = [{"episode_title": "EP1", "podcast_title": "Pod",
        ...            "chunk_transcript": "text...", "similarity": 0.95}]
        >>> ctx = build_context(chunks)
        >>> "Episode Title:" in ctx
        True
    """
    context = ""
    for chunk in retrieved_chunks:
        similarity = chunk.get("similarity")
        similarity_str = f"{similarity:.2f}" if similarity is not None else "N/A"
        context += f"""
                    Episode Title: {chunk.get("episode_title", "N/A")}
                    Podcast Title: {chunk.get("podcast_title", "N/A")}
                    Similarity: {similarity_str}

                    {chunk.get("chunk_transcript", "N/A")}

                    ---
                    """
    return context


def generate_response(
    client: OpenAI, user_query: str, context: str, model: str = "gpt-4o-mini"
) -> str:
    """Generate an answer using OpenAI API with retrieved context.

    Args:
        client: Initialized OpenAI client.
        user_query: The user's original question.
        context: Retrieved podcast context to use for answering.
        model: LLM model to use (default: gpt-4o-mini).

    Returns:
        Generated response from the LLM.

    Raises:
        OpenAIError: If API request fails.

    Example:
        >>> client = get_openai_client()
        >>> response = generate_response(client, "What about AI?", "Context...")
        >>> len(response) > 0
        True
    """
    prompt = f"""Based on the following podcast transcript excerpts, answer the user's question.

Context:
{context}

User Question: {user_query}

Please provide a helpful, accurate answer based on the context provided."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        if not response.choices:
            raise ValueError("No response choices returned from chat completion")

        content = response.choices[0].message.content
        return content or "I could not generate a response from the retrieved context."
    except OpenAIError as e:
        logger.error("Failed to generate response: %s", e)
        raise


def answer_query(
    user_query: str,
    top_k: int = 10,
    similarity_threshold: float = 0.5,
) -> str:
    """Orchestrate the full RAG pipeline to answer a user query.

    Performs the following steps:
    1. Embeds the user query
    2. Retrieves the top-k most similar chunks above similarity threshold
    3. Builds context from retrieved chunks
    4. Generates a response using the LLM

    Args:
        user_query: The user's natural language question about podcasts.
        top_k: Number of most similar chunks to retrieve (default: 10).
        similarity_threshold: Minimum similarity score to include (default: 0.5).

    Returns:
        Generated response answering the user's question based on podcast content.

    Raises:
        ValueError: If OpenAI API key is not set or query embedding fails.
        Exception: If database connection or retrieval fails.
        OpenAIError: If response generation fails.

    Example:
        >>> response = answer_query("What are the latest trends in AI?")
        >>> len(response) > 0
        True
    """
    logger.info("Processing user query: %s", user_query)

    # Initialize clients
    openai_client = get_openai_client()
    db_conn = get_db_connection()

    try:
        # Step 1: Embed the query
        logger.info("Step 1: Embedding user query...")
        query_embedding = get_query_embedding(openai_client, user_query)

        # Step 2: Retrieve similar chunks
        logger.info(
            "Step 2: Retrieving similar chunks (top_k=%d, threshold=%.2f)...",
            top_k,
            similarity_threshold,
        )
        retrieved_chunks = query_similar_chunks(
            db_conn,
            query_embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        if not retrieved_chunks:
            logger.warning("No relevant chunks found for query: %s", user_query)
            return (
                "I couldn't find relevant information "
                "in the podcast transcripts to answer your question."
            )

        # Step 3: Build context
        logger.info("Step 3: Building context from %d chunks...", len(retrieved_chunks))
        context = build_context(retrieved_chunks)

        # Step 4: Generate response
        logger.info("Step 4: Generating response...")
        response = generate_response(openai_client, user_query, context)

        logger.info("Successfully answered query")
        return response
    except Exception as e:
        logger.error("Error generating answer: %s", str(e))
        raise
    finally:
        db_conn.close()


if __name__ == "__main__":
    # Example usage
    load_dotenv()  # Load environment variables from .env file
    query = "What brands are discussed alongside sustainability?"

    try:
        answer = answer_query(query, similarity_threshold=0.5)
        print("Answer:\n", answer)
    except Exception as e:
        print("Failed to generate answer:", str(e))
