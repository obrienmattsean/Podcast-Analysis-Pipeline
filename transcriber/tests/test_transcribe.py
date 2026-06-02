"""Unit tests for transcribe module."""

from pydub import AudioSegment
from transcribe import _split_audio_into_chunks


class TestSplitAudioIntoChunks:
    def test_split_audio_into_chunks_returns_correct_number_of_chunks(self):
        audio = AudioSegment.silent(duration=30 * 60 * 1000)  # 30 minutes

        chunks = _split_audio_into_chunks(audio, chunk_length_minutes=10)

        assert len(chunks) == 3

    def test_split_audio_into_chunks_each_chunk_has_correct_duration(self):
        chunk_length_minutes = 10
        audio = AudioSegment.silent(duration=chunk_length_minutes * 60 * 1000)

        chunks = _split_audio_into_chunks(audio, chunk_length_minutes=chunk_length_minutes)

        assert len(chunks[0]) == chunk_length_minutes * 60 * 1000

    def test_split_audio_into_chunks_last_chunk_is_shorter_when_not_evenly_divisible(self):
        audio = AudioSegment.silent(duration=25 * 60 * 1000)  # 25 minutes

        chunks = _split_audio_into_chunks(audio, chunk_length_minutes=10)

        assert len(chunks) == 3
        assert len(chunks[-1]) == 5 * 60 * 1000  # 5 minute remainder

    def test_split_audio_into_chunks_single_chunk_when_audio_fits(self):
        audio = AudioSegment.silent(duration=5 * 60 * 1000)  # 5 minutes

        chunks = _split_audio_into_chunks(audio, chunk_length_minutes=10)

        assert len(chunks) == 1
        assert len(chunks[0]) == 5 * 60 * 1000
