
CREATE EXTENSION IF NOT EXISTS vector;

-- Podcasts table: stores podcast metadata
CREATE TABLE IF NOT EXISTS podcasts (
  id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  rss_url VARCHAR(500) UNIQUE NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Episodes table: stores individual podcast episodes
CREATE TABLE IF NOT EXISTS episodes (
  id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  podcast_id INTEGER NOT NULL REFERENCES podcasts(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  audio_url VARCHAR(500) NOT NULL,
  duration_seconds INTEGER,
  pub_date TIMESTAMP NOT NULL,
  sentient_score FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entities table: stores entities (persons, organizations, concepts, etc.)
CREATE TABLE IF NOT EXISTS entities (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  entity_type VARCHAR(100) NOT NULL  -- e.g., "Person", "Organization", "Concept"
);

-- Episode_entities: stores the unique combination of entity and episode
CREATE TABLE IF NOT EXISTS episode_entities (
  episode_id INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  entity_id INTEGER NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
  UNIQUE(episode_id, entity_id)
);

-- Segments table: breaks episodes into chunks for analysis
CREATE TABLE IF NOT EXISTS episode_chunks (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  episode_id INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  start_time_seconds INTEGER,
  end_time_seconds INTEGER,
  content TEXT,
  embedding vector(1536),  -- ALTER THE SIZE OF VECTOR
  chunk_transcript TEXT
);





-- ==============================================================================
-- Permissions (Create these after creating roles)
-- ==============================================================================
-- These commands assume you have created roles like 'podcast_app_user'
-- Uncomment and run after creating roles:

-- Grant read access to application role
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO podcast_app_user;

-- Grant insert/update access for data ingestion
-- GRANT INSERT, UPDATE ON podcasts, episodes, episode_chunks, entities, episode_entities TO podcast_app_user;

-- Grant vector search access
-- GRANT SELECT ON episode_embeddings, episode_topics TO podcast_app_user;

-- ==============================================================================
