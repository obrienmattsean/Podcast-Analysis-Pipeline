"""Upload functions for the Podcast Analysis Pipeline.

This module creates all the upload functions for the Podcast Analysis Pipeline
for reference in the completed script. Uploads are performed by interacting with
the PostgreSQL database to store the enriched podcast transcripts.

Example:
    Typical usage example:

        from enrich_upload.enrichment_functions import some_function
        some_function(input_data)

"""

import logging
from datetime import datetime

import dotenv
import psycopg2

dotenv.load_dotenv()


def combine_enrichments(episode_metadata: dict, enrichments: dict) -> dict:
    """Combines all the enrichments into a single dictionary to be uploaded to RDS.

    Args:
        episode_metadata (dict): The metadata of the episode.
        enrichments (dict): The enrichments generated from the episode transcript.

    Returns:
        dict: A dictionary containing all the enrichments and metadata to be uploaded to RDS.

    """

    # Create dictionaries for each table in RDS

    published_at = episode_metadata.get("published_at")
    episode = {
        "episode_id": episode_metadata.get("episode_id"),
        "podcast_id": episode_metadata.get("podcast_id"),
        "title": episode_metadata.get("title"),
        "audio_url": episode_metadata.get("audio_link"),
        "pub_date": published_at[:10] if published_at else None,
        "duration_seconds": None,
        "sentiment_score": enrichments.get("sentiment score"),
        "created_at": datetime.now(),
        "summary": enrichments.get("summary"),
    }

    entities = {}
    for entity in enrichments.get("keywords", []):
        entities[entity[0] + entity[1]] = {"name": entity[0], "entity_type": entity[1]}
    for host in enrichments.get("hosts", []):
        entities[host] = {"name": host, "entity_type": "host"}
    for guest in enrichments.get("guests", []):
        entities[guest] = {"name": guest, "entity_type": "guest"}

    combined = {"episode": episode, "entities": entities}
    return combined


def upload_to_rds(enrichment_dict: dict, db_connection: psycopg2.extensions.connection) -> None:
    """Uploads the full enriched data to RDS.

    Args:
        enrichment_dict (dict): The dictionary containing all the enrichments to be
        uploaded to RDS. db_connection (psycopg2.extensions.connection): The
        connection object to the PostgreSQL database.

    Returns:
        None

    """

    cursor = None
    try:
        cursor = db_connection.cursor()

        # Insert episode data
        episode_data = enrichment_dict["episode"]
        logging.info(f"Episode data uploading: {episode_data['episode_id']}")
        cursor.execute(
            """
            UPDATE episodes
            SET sentiment_score = %s,
            summary = %s
            WHERE id = %s;
        """,
            (episode_data["sentiment_score"], episode_data["summary"], episode_data["episode_id"]),
        )

        # Insert entities data
        entities_data = enrichment_dict["entities"]
        logging.info("Entities data uploading")
        for entity_info in entities_data.values():
            cursor.execute(
                """
                INSERT INTO entities (name, entity_type)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING;
            """,
                (entity_info["name"], entity_info["entity_type"]),
            )

        # Insert episode_entities data
        episode_entities = enrichment_dict["entities"]
        logging.info("Episode entities data uploading")
        for entity in episode_entities.values():
            cursor.execute(
                """
            INSERT INTO episode_entities (episode_id, entity_id)
            VALUES (%s, (SELECT entity_id FROM entities WHERE name = %s AND entity_type = %s))
            ON CONFLICT DO NOTHING;""",
                (enrichment_dict["episode"]["episode_id"], entity["name"], entity["entity_type"]),
            )

        db_connection.commit()
        cursor.close()

    except Exception as e:
        logging.error(f"Failed to upload data to RDS: {e}")
        if cursor:
            cursor.close()
        if db_connection:
            db_connection.rollback()
        raise
