"""AI Search page with RAG chatbot for semantic podcast search.

This page provides an interactive chatbot interface powered by a Retrieval-Augmented
Generation (RAG) pipeline that searches podcast transcripts semantically.
"""

import logging

import streamlit as st
from dotenv import load_dotenv
from rag.convert import get_openai_client, get_query_embedding
from rag.generator import answer_query
from rag.retrieval import get_db_connection, query_similar_chunks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="AI Search", layout="wide")
st.header("🎙️ AI Search - Podcast RAG Chatbot")
st.write(
    "Ask questions about podcast content using semantic search powered by AI. "
    "The chatbot will search through episode transcripts and provide relevant answers."
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "retrieved_chunks" not in st.session_state:
    st.session_state.retrieved_chunks = None


# Sidebar configuration
with st.sidebar:
    st.subheader("⚙️ Settings")

    top_k = st.slider(
        "Number of chunks to retrieve",
        min_value=3,
        max_value=20,
        value=10,
        help="How many relevant podcast chunks to retrieve for context",
    )

    similarity_threshold = st.slider(
        "Similarity threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Minimum similarity score for chunks to be included",
    )

    show_sources = st.checkbox(
        "Show retrieved sources",
        value=True,
        help="Display the podcast chunks used to generate the answer",
    )


# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# Chat input
if prompt := st.chat_input("Ask a question about the podcasts..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response with error handling
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()

        try:
            status_placeholder.info("🔍 Searching podcast transcripts...")

            # Call the RAG pipeline
            response = answer_query(
                user_query=prompt, top_k=top_k, similarity_threshold=similarity_threshold
            )

            status_placeholder.empty()
            message_placeholder.markdown(response)

            # Add assistant message to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Store retrieval info for display
            st.session_state.retrieved_chunks = {
                "query": prompt,
                "top_k": top_k,
                "threshold": similarity_threshold,
                "response_length": len(response),
            }

        except ValueError as e:
            error_msg = f"⚠️ Configuration Error: {str(e)}"
            status_placeholder.empty()
            message_placeholder.error(error_msg)
            logger.error(error_msg)

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            status_placeholder.empty()
            message_placeholder.error(error_msg)
            logger.error(f"Failed to generate response: {error_msg}")


# Display retrieved sources if enabled
if show_sources and st.session_state.retrieved_chunks:
    st.divider()
    st.subheader("📚 Retrieved Context")

    with st.expander("View retrieved chunks"):
        try:
            # Retrieve chunks to display
            openai_client = get_openai_client()
            db_conn = get_db_connection()

            query_embedding = get_query_embedding(
                openai_client, st.session_state.retrieved_chunks["query"]
            )
            retrieved_chunks = query_similar_chunks(
                db_conn,
                query_embedding,
                top_k=st.session_state.retrieved_chunks["top_k"],
                similarity_threshold=st.session_state.retrieved_chunks["threshold"],
            )
            db_conn.close()

            if retrieved_chunks:
                for idx, chunk in enumerate(retrieved_chunks, 1):
                    with st.container():
                        col1, col2 = st.columns([3, 1])

                        with col1:
                            st.write(f"**Chunk {idx}**")
                            st.caption(f"📻 {chunk['podcast_title']} → 🎬 {chunk['episode_title']}")
                            st.markdown(f"> {chunk['chunk_transcript'][:200]}...")

                        with col2:
                            similarity_score = chunk.get("similarity", 0)
                            st.metric("Similarity", f"{similarity_score:.2%}")

                        st.divider()
            else:
                st.info("No relevant chunks found for this query.")

        except Exception as e:
            st.warning(f"Could not retrieve source information: {str(e)}")


# Footer with instructions
st.divider()
with st.expander("💡 How to use the RAG Chatbot"):
    st.markdown("""
    ### Getting Started
    1. **Ask a question** about any topic related to the podcasts
    2. **Adjust settings** in the sidebar to fine-tune the search:
       - **Number of chunks**: More chunks = more context but slower response
       - **Similarity threshold**: Higher threshold = more relevant but fewer results
    3. **View sources**: Enable "Show retrieved sources" to see which podcast segments were used

    ### Tips for Better Results
    - Use natural language questions
    - Be specific about what you're looking for
    - Use keywords from the podcasts if you know them
    - Adjust the similarity threshold if results aren't relevant enough

    ### Example Questions
    - "What brands are discussed alongside sustainability?"
    - "Which episodes discuss AI applications?"
    - "What are the main topics covered?"
    """)
