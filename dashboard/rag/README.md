# 🎙️ RAG Chatbot for AI Search

This is a Retrieval-Augmented Generation (RAG) chatbot integrated into the dashboard's AI Search page. It enables semantic search over podcast transcripts and provides intelligent answers using OpenAI's language models.

## Features

- **Semantic Search**: Uses OpenAI embeddings to semantically search podcast transcripts
- **Interactive Chat**: Built-in Streamlit chat interface with conversation history
- **Source Attribution**: Shows which podcast episodes were used to generate answers
- **Configurable Parameters**: Adjust similarity thresholds and chunk count for fine-tuned results
- **Error Handling**: Graceful error handling with informative messages

## Architecture

The RAG pipeline consists of three main components:

### 1. **convert.py** - Embedding Generation
- Converts user queries into embedding vectors using OpenAI's `text-embedding-3-small` model
- Manages OpenAI client initialization

### 2. **retrieval.py** - Vector Search
- Queries PostgreSQL with pgvector extension for semantically similar chunks
- Filters results by cosine similarity threshold
- Returns top-k most relevant podcast segments

### 3. **generator.py** - Response Generation
- Orchestrates the full RAG pipeline
- Builds context from retrieved chunks
- Generates answers using OpenAI's chat completion API
- System prompt guides the model to cite sources and stay grounded in podcast content

## Setup

### Prerequisites
- Python 3.8+
- PostgreSQL with pgvector extension
- OpenAI API key
- AWS RDS PostgreSQL instance (for production)

### Installation

1. **Install Dependencies**
   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env with your credentials
   export OPENAI_API_KEY="your-api-key"
   export RDS_HOST="your-rds-host"
   export RDS_DBNAME="your-database"
   export RDS_USER="postgres"
   export RDS_PASSWORD="your-password"
   export RDS_PORT="5432"
   ```

3. **Run the Dashboard**
   ```bash
   streamlit run app.py
   ```

4. **Access AI Search**
   Navigate to the "AI Search" page (Page 2) in the dashboard sidebar

## Usage

### Basic Usage
1. Type a question in the chat input field
2. The chatbot will:
   - Embed your query
   - Search for similar podcast chunks
   - Generate an answer based on the retrieved context
   - Display the response in the chat

### Configuration Options (Sidebar)

- **Number of chunks to retrieve** (3-20, default: 10)
  - Higher values = more context but slower responses

- **Similarity threshold** (0.0-1.0, default: 0.5)
  - Higher threshold = more relevant results but fewer chunks
  - Lower threshold = more chunks but potentially less relevant

- **Show retrieved sources** (checkbox, default: enabled)
  - When enabled, displays the podcast segments used for the answer

### Example Questions
- "What brands are discussed alongside sustainability?"
- "Which episodes discuss AI applications?"
- "What are the main topics covered?"
- "Tell me about the guests mentioned in the podcasts"

## How It Works

```
User Question
    ↓
Embed Query (OpenAI Embeddings)
    ↓
Search Similar Chunks (PostgreSQL + pgvector)
    ↓
Build Context (Format chunks for LLM)
    ↓
Generate Response (OpenAI Chat Completion)
    ↓
Display Answer with Sources
```

## Database Schema Requirements

Your PostgreSQL instance must have the following tables:

```sql
-- Podcasts table
CREATE TABLE podcasts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL
);

-- Episodes table
CREATE TABLE episodes (
    id SERIAL PRIMARY KEY,
    podcast_id INT REFERENCES podcasts(id),
    title VARCHAR(255) NOT NULL
);

-- Episode chunks with embeddings
CREATE TABLE episode_chunks (
    id SERIAL PRIMARY KEY,
    episode_id INT REFERENCES episodes(id),
    chunk_index INT NOT NULL,
    chunk_transcript TEXT NOT NULL,
    embedding vector(1536)  -- pgvector extension required
);

-- Vector index for performance
CREATE INDEX idx_chunk_embedding ON episode_chunks
USING ivfflat (embedding vector_cosine_ops);
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `RDS_HOST` | PostgreSQL host | `mydb.xxx.rds.amazonaws.com` |
| `RDS_PORT` | PostgreSQL port | `5432` |
| `RDS_DBNAME` | Database name | `podcast_db` |
| `RDS_USER` | Database user | `postgres` |
| `RDS_PASSWORD` | Database password | `****` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Performance Tuning

- **Slow responses?**
  - Reduce `top_k` parameter (fewer chunks to retrieve)
  - Increase similarity threshold to filter out marginal results

- **Poor answer quality?**
  - Lower the similarity threshold to include more context
  - Increase `top_k` for more comprehensive search results

- **Database queries timing out?**
  - Ensure pgvector index is created on `embedding` column
  - Consider creating a new vector index with different parameters

## Troubleshooting

### "OPENAI_API_KEY is not set"
- Ensure your `.env` file is in the dashboard directory
- Verify the key is correctly set: `echo $OPENAI_API_KEY`

### "No relevant chunks found"
- Lower the similarity threshold in sidebar settings
- Try rephrasing your question with different keywords
- Ensure podcast data and embeddings are in the database

### Database connection errors
- Verify RDS credentials are correct
- Check that your IP is whitelisted in the security group
- Ensure pgvector extension is installed: `CREATE EXTENSION vector;`

### Slow response times
- Check database performance (create index on embeddings)
- Reduce `top_k` parameter
- Check OpenAI API status

## Development

### Adding New Features
- Modify `2_AI_Search.py` for UI changes
- Update `generator.py` for RAG pipeline logic
- Modify `retrieval.py` for database queries

### Testing the RAG Pipeline
```python
from rag.generator import answer_query

# Test directly
response = answer_query("What are the main topics discussed?", top_k=10)
print(response)
```

## Contributing

When modifying the RAG components:
1. Follow the project's coding style guidelines (see root `.github/instructions/`)
2. Add type hints to all functions
3. Include docstrings in Google style format
4. Test with actual podcast data before deploying

## License

See root repository LICENSE file.
