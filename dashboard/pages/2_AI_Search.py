import logging

import streamlit as st
from dotenv import load_dotenv
from rag.convert import get_openai_client, get_query_embedding
from rag.generator import answer_query
from rag.retrieval import get_db_connection, query_similar_chunks

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AI Search",
    page_icon="🎙️",
    layout="wide",
)

# --------------------------------------------------
# CSS
# --------------------------------------------------

st.markdown(
    """
<style>

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}

.search-header {
    text-align: center;
    margin-bottom: 2rem;
}

.summary-card {
    padding: 1rem;
}

.result-card {
    padding: 1rem;
}

</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "results" not in st.session_state:
    st.session_state.results = None

if "query" not in st.session_state:
    st.session_state.query = ""

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.subheader("⚙️ Search Settings")

    top_k = st.slider(
        "Top K Results",
        min_value=5,
        max_value=50,
        value=15,
    )

    similarity_threshold = st.slider(
        "Similarity Threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.50,
        step=0.05,
    )

    show_sources = st.checkbox(
        "Show Transcript Evidence",
        value=True,
    )

# --------------------------------------------------
# SEARCH FUNCTION
# --------------------------------------------------


def run_search(query: str):

    with st.spinner("Searching podcast transcripts..."):
        answer = answer_query(
            user_query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        openai_client = get_openai_client()

        db_conn = get_db_connection()

        embedding = get_query_embedding(
            openai_client,
            query,
        )

        chunks = query_similar_chunks(
            db_conn,
            embedding,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        db_conn.close()

        st.session_state.results = {
            "query": query,
            "answer": answer,
            "chunks": chunks,
        }


# --------------------------------------------------
# EMPTY STATE
# --------------------------------------------------

if st.session_state.results is None:
    st.markdown(
        """
        <div class="search-header">
            <h1>AI Search</h1>
            <p>Search across podcast transcripts using semantic retrieval.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    placeholder_text = """Which podcasts discussed sustainability in the context
                            of consumer brands in the last 30 days?"""
    query = st.text_input(
        "",
        placeholder=placeholder_text,
        label_visibility="collapsed",
    )

    search_clicked = st.button(
        "✨ Search",
        use_container_width=True,
    )

    st.write("")

    suggestions = [
        "Which episodes mentioned Nike?",
        "Shows with negative sentiment this week",
        "Episodes covering programmatic advertising",
        "Podcasts safe for a family brand",
    ]

    cols = st.columns(2)

    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(
                suggestion,
                use_container_width=True,
                key=f"suggestion_{i}",
            ):
                run_search(suggestion)
                st.rerun()

    if search_clicked and query:
        run_search(query)
        st.rerun()

# --------------------------------------------------
# RESULTS STATE
# --------------------------------------------------

else:
    results = st.session_state.results

    st.title("AI Search")

    col1, col2 = st.columns([8, 1])

    with col1:
        query = st.text_input(
            "",
            value=results["query"],
            label_visibility="collapsed",
        )

    with col2:
        if st.button("Search"):
            run_search(query)
            st.rerun()

    chunks = results["chunks"]

    podcasts = set()
    episodes = {}

    for chunk in chunks:
        podcast = chunk.get("podcast_title", "Unknown")
        episode = chunk.get("episode_title", "Unknown")

        podcasts.add(podcast)

        key = (podcast, episode)

        if key not in episodes:
            episodes[key] = {
                "podcast": podcast,
                "episode": episode,
                "count": 0,
                "chunks": [],
            }

        episodes[key]["count"] += 1
        episodes[key]["chunks"].append(chunk)

    # ----------------------------------------------
    # SUMMARY CARD
    # ----------------------------------------------

    with st.container(border=True):
        st.caption("✨ PODEX AI SUMMARY")

        st.subheader(f"Found {len(episodes)} matching episodes across {len(podcasts)} podcasts")

        st.markdown(results["answer"])

    st.write("")

    st.subheader(f"{len(episodes)} Matched Episodes")

    sorted_episodes = sorted(
        episodes.values(),
        key=lambda x: x["count"],
        reverse=True,
    )

    # ----------------------------------------------
    # EPISODE CARDS
    # ----------------------------------------------

    for episode in sorted_episodes:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(f"### 🎙️ {episode['podcast']}")

                st.caption(episode["episode"])

            with col2:
                st.metric(
                    "Mentions",
                    episode["count"],
                )

            if show_sources:
                with st.expander("Transcript Evidence"):
                    for chunk in episode["chunks"]:
                        similarity = chunk.get(
                            "similarity",
                            0,
                        )

                        st.caption(f"Similarity: {similarity:.2%}")

                        st.markdown(f"> {chunk['chunk_transcript']}")

                        st.divider()

    # ----------------------------------------------
    # NEW SEARCH BUTTON
    # ----------------------------------------------

    st.write("")

    if st.button("← New Search"):
        st.session_state.results = None
        st.session_state.query = ""

        st.rerun()
