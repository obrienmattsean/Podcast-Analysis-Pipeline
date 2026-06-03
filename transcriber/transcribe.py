"""Chunked audio transcription utilities for podcast episodes."""

import os
from collections.abc import Iterable
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment

load_dotenv()


def transcribe(
    audio_path: Path,
    model: str = "whisper-1",
    chunk_length_minutes: int = 10,
) -> str:
    """Transcribe an audio file using the OpenAI API.

    Automatically splits files longer than ``chunk_length_minutes`` into
    smaller chunks and concatenates the results.

    Args:
        audio_path: Path to the audio file to transcribe.
        model: Transcription model identifier.
        chunk_length_minutes: Maximum chunk duration in minutes before the
            audio is split for transcription.

    Returns:
        str: Transcribed text from the audio.
    """
    openai_client = _get_openai_client()
    duration_minutes = _get_audio_duration_minutes(audio_path)
    if duration_minutes > chunk_length_minutes:
        chunks = _split_audio_into_chunks(AudioSegment.from_file(audio_path), chunk_length_minutes)
        return _transcribe_chunks(chunks, openai_client, model)
    transcription = openai_client.audio.transcriptions.create(file=audio_path, model=model)
    return transcription.text.strip()


def _transcribe_chunks(
    chunks: Iterable[AudioSegment], openai_client: OpenAI, model: str = "whisper-1"
) -> str:
    """Transcribe multiple audio chunks and concatenate the results.

    Args:
        chunks: Iterable of audio segments to transcribe.
        openai_client: Initialized OpenAI client.
        model: Transcription model identifier.

    Returns:
        str: Concatenated transcription text from all chunks
    """

    full_transcript = ""
    for chunk in chunks:
        chunk_file_path = Path("/tmp") / "chunk.mp3"
        chunk.export(chunk_file_path, format="mp3")
        chunk_transcript = transcribe(chunk_file_path, model)
        full_transcript += chunk_transcript + "\n"
    return full_transcript.strip()


def _get_openai_client() -> OpenAI:
    """Create an OpenAI client from environment configuration.

    Returns:
        OpenAI: Configured OpenAI client instance.
    """

    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _split_audio_into_chunks(audio: AudioSegment, chunk_length_minutes: int) -> list[AudioSegment]:
    """Split an audio segment into fixed-duration chunks.

    Args:
        audio: Source audio segment to split.
        chunk_length_minutes: Chunk duration in minutes.

    Returns:
        list[AudioSegment]: Audio chunks in original order.
    """

    chunk_length_ms = chunk_length_minutes * 60 * 1000
    return [audio[i : i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]


def _get_audio_duration_minutes(audio_path: Path) -> float:
    """Calculate the duration of an audio file in minutes.

    Args:
        audio_path: Path to the audio file.

    Returns:
        float: Duration of the audio file in minutes.
    """
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / (60 * 1000)
