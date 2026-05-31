import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import load  # noqa: E402


class TestSerializeEpisode:
    def test_converts_episode_to_dict(self, validated_episode):
        episode = validated_episode()
        result = load.serialize_episode(episode)

        assert result["podcast_id"] == 1
        assert result["title"] == "Test Episode"
        assert result["audio_link"] == "https://example.com/ep.mp3"
        assert result["published_at"] == "2026-05-01T00:00:00"

    def test_converts_datetime_to_isoformat(self, validated_episode):
        pub_date = datetime(2026, 5, 15, 0, 0, 0)
        episode = validated_episode(published_at=pub_date)
        result = load.serialize_episode(episode)

        assert result["published_at"] == "2026-05-15T00:00:00"

    def test_converts_audio_link_to_string(self, validated_episode):
        episode = validated_episode(audio_link="https://cdn.example.com/episodes/ep.m4a")
        result = load.serialize_episode(episode)

        assert isinstance(result["audio_link"], str)
        assert result["audio_link"] == "https://cdn.example.com/episodes/ep.m4a"


class TestInsertEpisodesToDb:
    def test_enriches_episodes_with_ids(self, validated_episode):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.fetchone.side_effect = [(101,), (102,)]
        conn.cursor.return_value = cursor

        episodes = [
            {
                "podcast_id": 1,
                "title": "Ep1",
                "audio_link": "https://example.com/ep1.mp3",
                "published_at": "2026-05-01T00:00:00",
            },
            {
                "podcast_id": 1,
                "title": "Ep2",
                "audio_link": "https://example.com/ep2.mp3",
                "published_at": "2026-05-01T00:00:00",
            },
        ]

        result = load._insert_episodes_to_db(conn, episodes)

        assert len(result) == 2
        assert result[0]["episode_id"] == 101
        assert result[1]["episode_id"] == 102
        assert conn.commit.call_count == 2

    def test_skips_failed_inserts_and_rolls_back(self):
        conn = MagicMock()
        cursor = MagicMock()
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        cursor.execute.side_effect = [Exception("DB error"), None]
        cursor.fetchone.return_value = (99,)
        conn.cursor.return_value = cursor

        episodes = [
            {
                "podcast_id": 1,
                "title": "Bad",
                "audio_link": "https://example.com/ep.mp3",
                "published_at": "2026-05-01",
            },
            {
                "podcast_id": 1,
                "title": "Good",
                "audio_link": "https://example.com/ep.mp3",
                "published_at": "2026-05-01",
            },
        ]

        result = load._insert_episodes_to_db(conn, episodes)

        assert len(result) == 1
        assert result[0]["title"] == "Good"
        conn.rollback.assert_called_once()

    def test_returns_empty_for_empty_input(self):
        conn = MagicMock()
        result = load._insert_episodes_to_db(conn, [])
        assert result == []
        conn.cursor.assert_not_called()


class TestBuildEpisodeListPayload:
    @patch("load._insert_episodes_to_db")
    def test_serializes_and_inserts_episodes(self, mock_insert, validated_episode):
        enriched = [
            {
                "podcast_id": 1,
                "title": "Ep1",
                "audio_link": "https://example.com/ep.mp3",
                "published_at": "2026-05-01T00:00:00",
                "episode_id": 101,
            },
            {
                "podcast_id": 1,
                "title": "Ep2",
                "audio_link": "https://example.com/ep.mp3",
                "published_at": "2026-05-01T00:00:00",
                "episode_id": 102,
            },
        ]
        mock_insert.return_value = enriched
        conn = MagicMock()
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Pod A",
            "new_episodes": [validated_episode(title="Ep1"), validated_episode(title="Ep2")],
        }

        result = load.build_episode_list_payload(conn, podcast_data)

        assert len(result) == 2
        assert result[0]["episode_id"] == 101
        assert result[1]["episode_id"] == 102
        mock_insert.assert_called_once()

    def test_returns_empty_when_no_episodes(self):
        conn = MagicMock()
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Pod A",
            "new_episodes": [],
        }

        result = load.build_episode_list_payload(conn, podcast_data)

        assert result == []

    def test_returns_empty_when_missing_episodes_key(self):
        conn = MagicMock()
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Pod A",
        }

        result = load.build_episode_list_payload(conn, podcast_data)

        assert result == []


class TestUploadPodcastPayloadToS3:
    def test_uploads_json_to_s3(self):
        mock_s3 = MagicMock()
        episodes = [
            {
                "podcast_id": 1,
                "title": "Ep1",
                "audio_link": "https://example.com/ep1.mp3",
                "episode_id": 101,
            },
            {
                "podcast_id": 1,
                "title": "Ep2",
                "audio_link": "https://example.com/ep2.mp3",
                "episode_id": 102,
            },
        ]

        paths = load.upload_podcast_payload_to_s3(mock_s3, "test-bucket", 1, episodes)
        assert mock_s3.put_object.call_count == 2
        first_call = mock_s3.put_object.call_args_list[0][1]
        second_call = mock_s3.put_object.call_args_list[1][1]
        assert first_call["Bucket"] == "test-bucket"
        assert first_call["Key"] == "1/101/metadata.json"
        assert first_call["ContentType"] == "application/json"
        assert json.loads(first_call["Body"]) == episodes[0]
        assert second_call["Key"] == "1/102/metadata.json"
        assert json.loads(second_call["Body"]) == episodes[1]
        assert paths == [
            "s3://test-bucket/1/101/",
            "s3://test-bucket/1/102/",
        ]

    def test_uploads_with_correct_s3_key_format(self):
        mock_s3 = MagicMock()
        episodes = [{"title": "Ep", "episode_id": 77}]

        paths = load.upload_podcast_payload_to_s3(mock_s3, "bucket", 42, episodes)

        call_kwargs = mock_s3.put_object.call_args[1]
        assert call_kwargs["Key"] == "42/77/metadata.json"
        assert paths == ["s3://bucket/42/77/"]

    def test_uploads_empty_episodes_list(self):
        mock_s3 = MagicMock()
        episodes = []

        paths = load.upload_podcast_payload_to_s3(mock_s3, "bucket", 1, episodes)
        mock_s3.put_object.assert_not_called()
        assert paths == []


class TestLoadPodcastEpisodes:
    @patch("load.upload_podcast_payload_to_s3")
    @patch("load.build_episode_list_payload")
    def test_returns_uploaded_and_failed_counts(self, mock_build, mock_upload, validated_episode):
        enriched = [
            {"title": "Ep1", "episode_id": 1},
            {"title": "Ep2", "episode_id": 2},
        ]
        mock_build.return_value = enriched
        mock_upload.return_value = [
            "s3://bucket/1/1/metadata.json",
            "s3://bucket/1/2/metadata.json",
        ]
        conn, s3 = MagicMock(), MagicMock()
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Pod A",
            "new_episodes": [validated_episode(), validated_episode()],
        }

        uploaded, failed, uploaded_paths = load.load_podcast_episodes(
            conn, s3, "bucket", podcast_data
        )

        assert uploaded == 2
        assert failed == 0
        assert uploaded_paths == [
            "s3://bucket/1/1/metadata.json",
            "s3://bucket/1/2/metadata.json",
        ]
        mock_upload.assert_called_once()

    @patch("load.build_episode_list_payload")
    def test_counts_partial_db_failures(self, mock_build, validated_episode):
        mock_build.return_value = [{"title": "Ep1", "episode_id": 1}]
        conn, s3 = MagicMock(), MagicMock()
        podcast_data = {
            "podcast_id": 1,
            "podcast_title": "Pod A",
            "new_episodes": [validated_episode(), validated_episode(), validated_episode()],
        }

        uploaded, failed, uploaded_paths = load.load_podcast_episodes(
            conn, s3, "bucket", podcast_data
        )

        assert uploaded == 1
        assert failed == 2
        assert uploaded_paths == ["s3://bucket/1/1/"]

    def test_returns_zero_counts_for_empty_episodes(self):
        conn, s3 = MagicMock(), MagicMock()
        podcast_data = {"podcast_id": 1, "new_episodes": []}

        uploaded, failed, uploaded_paths = load.load_podcast_episodes(
            conn, s3, "bucket", podcast_data
        )

        assert uploaded == 0
        assert failed == 0
        assert uploaded_paths == []

    @patch("load.upload_podcast_payload_to_s3")
    @patch("load.build_episode_list_payload")
    def test_returns_zero_on_s3_failure(self, mock_build, mock_upload, validated_episode):
        mock_build.return_value = [{"title": "Ep1", "episode_id": 1}]
        mock_upload.side_effect = Exception("S3 error")
        conn, s3 = MagicMock(), MagicMock()
        podcast_data = {
            "podcast_id": 1,
            "new_episodes": [validated_episode()],
        }

        uploaded, failed, uploaded_paths = load.load_podcast_episodes(
            conn, s3, "bucket", podcast_data
        )

        assert uploaded == 0
        assert failed == 1
        assert uploaded_paths == []


class TestLoadAllEpisodes:
    @patch("load.load_podcast_episodes")
    def test_sums_counts_across_podcasts(self, mock_load_podcast):
        mock_load_podcast.side_effect = [
            (2, 0, ["s3://bucket/1/10", "s3://bucket/1/11"]),
            (1, 1, ["s3://bucket/2/21"]),
        ]
        conn, s3 = MagicMock(), MagicMock()
        entries = [
            {"podcast_id": 1, "new_episodes": [MagicMock(), MagicMock()]},
            {"podcast_id": 2, "new_episodes": [MagicMock(), MagicMock()]},
        ]

        uploaded_paths = load.load_all_episodes(conn, s3, entries, bucket="bucket")

        assert mock_load_podcast.call_count == 2
        assert uploaded_paths == [
            "s3://bucket/1/10",
            "s3://bucket/1/11",
            "s3://bucket/2/21",
        ]

    @patch("load.load_podcast_episodes")
    def test_processes_all_podcasts_even_if_one_fails(self, mock_load_podcast):
        mock_load_podcast.side_effect = [
            (2, 0, ["s3://bucket/1/1", "s3://bucket/1/2"]),
            (0, 2, []),
            (1, 0, ["s3://bucket/3/3"]),
        ]
        conn, s3 = MagicMock(), MagicMock()
        entries = [
            {"podcast_id": 1, "new_episodes": [MagicMock()]},
            {"podcast_id": 2, "new_episodes": [MagicMock()]},
            {"podcast_id": 3, "new_episodes": [MagicMock()]},
        ]

        uploaded_paths = load.load_all_episodes(conn, s3, entries, bucket="bucket")

        assert mock_load_podcast.call_count == 3
        assert uploaded_paths == [
            "s3://bucket/1/1",
            "s3://bucket/1/2",
            "s3://bucket/3/3",
        ]
