CREATE EXTENSION IF NOT EXISTS vector;


DROP TABLE IF EXISTS episode_chunks CASCADE;
DROP TABLE IF EXISTS episode_entities CASCADE;
DROP TABLE IF EXISTS entities CASCADE;
DROP TABLE IF EXISTS episodes CASCADE;
DROP TABLE IF EXISTS podcasts CASCADE;


CREATE TABLE podcasts (
    podcast_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    rss_url VARCHAR(500) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE episodes (
    episode_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    podcast_id INTEGER NOT NULL REFERENCES podcasts(podcast_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    audio_url VARCHAR(500) NOT NULL,
    duration_seconds INTEGER,
    pub_date TIMESTAMP NOT NULL,
    sentiment_score DOUBLE PRECISION,
    brand_safety_score INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    summary TEXT
);

CREATE INDEX idx_episodes_podcast_id
    ON episodes(podcast_id);

CREATE INDEX idx_episodes_pub_date
    ON episodes(pub_date);


CREATE TABLE entities (
    entity_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    entity_type VARCHAR(100) NOT NULL
);


CREATE TABLE episode_entities (
    episode_id INTEGER NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,
    entity_id INTEGER NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,

    PRIMARY KEY (episode_id, entity_id)
);


CREATE TABLE episode_chunks (
    episode_chunk_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    episode_id INTEGER NOT NULL REFERENCES episodes(episode_id) ON DELETE CASCADE,

    chunk_index INTEGER NOT NULL,

    start_time_seconds INTEGER,
    end_time_seconds INTEGER,

    content TEXT,
    chunk_transcript TEXT NOT NULL,

    embedding VECTOR(1536) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_episode_chunk
        UNIQUE (episode_id, chunk_index)
);

CREATE INDEX idx_episode_chunks_episode_id
    ON episode_chunks(episode_id);