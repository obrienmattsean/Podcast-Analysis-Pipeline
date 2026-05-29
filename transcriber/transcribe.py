"""Chunked audio transcription utilities for podcast episodes."""

import os
from collections.abc import Iterable
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment

load_dotenv()


def get_openai_client() -> OpenAI:
    """Create an OpenAI client from environment configuration.

    Returns:
        OpenAI: Configured OpenAI client instance.
    """

    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def split_audio(audio: AudioSegment, chunk_length_minutes: int = 10) -> list[AudioSegment]:
    """Split an audio segment into fixed-duration chunks.

    Args:
        audio: Source audio segment to split.
        chunk_length_minutes: Chunk duration in minutes.

    Returns:
        list[AudioSegment]: Audio chunks in original order.
    """

    chunk_length_ms = chunk_length_minutes * 60 * 1000
    chunks = []
    for i in range(0, len(audio), chunk_length_ms):
        chunk = audio[i : i + chunk_length_ms]
        chunks.append(chunk)
    return chunks


def export_chunks_to_mp3(chunks: list[AudioSegment], output_dir: Path) -> list[Path]:
    """Export audio chunks as numbered MP3 files.

    Args:
        chunks: Audio chunks to export.
        output_dir: Directory where chunk files are written.

    Returns:
        list[Path]: Paths to exported chunk files in order.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    chunk_paths: list[Path] = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_path = output_dir / f"chunk_{index:04d}.mp3"
        chunk.export(chunk_path, format="mp3")
        chunk_paths.append(chunk_path)
    return chunk_paths


def get_audio_duration_minutes(audio: AudioSegment) -> int:
    """Return audio duration rounded down to whole minutes.

    Args:
        audio: Audio segment whose duration is measured.

    Returns:
        int: Duration in whole minutes.
    """

    return int(audio.duration_seconds / 60)


def transcribe_audio_file(audio_path: Path, openai_client: OpenAI, model: str) -> str:
    """Transcribe a single local audio file.

    Args:
        audio_path: Local path to an audio file.
        openai_client: Initialized OpenAI client.
        model: Transcription model identifier.

    Returns:
        str: Plain-text transcription result.
    """

    with audio_path.open("rb") as audio_file:
        transcription = openai_client.audio.transcriptions.create(
            file=audio_file,
            model=model,
            response_format="text",
        )
    if isinstance(transcription, str):
        return transcription
    return transcription.text


def transcribe_chunks(chunk_paths: Iterable[Path], openai_client: OpenAI, model: str) -> str:
    """Transcribe chunk files and merge into one normalized text string.

    Args:
        chunk_paths: Iterable of chunk file paths in playback order.
        openai_client: Initialized OpenAI client.
        model: Transcription model identifier.

    Returns:
        str: Combined transcript with normalized whitespace.
    """

    transcript_sections: list[str] = []
    for chunk_path in chunk_paths:
        transcript = transcribe_audio_file(chunk_path, openai_client, model).strip()
        transcript_sections.append(transcript)
    return " ".join(" ".join(transcript_sections).split())


def write_transcript(transcript: str, output_path: Path) -> None:
    """Write transcript text to disk as UTF-8.

    Args:
        transcript: Transcript content to persist.
        output_path: Destination text file path.
    """

    output_path.write_text(transcript, encoding="utf-8")


def transcribe_audio_to_text(
    source_audio_path: Path,
    chunks_output_dir: Path,
    transcribe_model: str,
    chunk_length_minutes: int = 10,
) -> str:
    """Transcribe a local audio file into one continuous text transcript.

    Args:
        source_audio_path: Local input audio file path.
        chunks_output_dir: Directory where intermediate chunk MP3s are written.
        transcribe_model: Transcription model identifier.
        chunk_length_minutes: Chunk duration in minutes.

    Returns:
        str: Full transcript as normalized plain text.
    """

    podcast = AudioSegment.from_mp3(source_audio_path)
    print(f"Podcast duration: {get_audio_duration_minutes(podcast)} minutes")

    chunks = split_audio(podcast, chunk_length_minutes=chunk_length_minutes)
    chunk_paths = export_chunks_to_mp3(chunks, chunks_output_dir)

    client = get_openai_client()
    print(f"Saved {len(chunk_paths)} chunks to {chunks_output_dir}")
    return transcribe_chunks(chunk_paths, client, transcribe_model)


def transcribe_source_audio(
    source_audio_path: Path,
    chunks_output_dir: Path,
    transcript_output_path: Path,
    transcribe_model: str,
    chunk_length_minutes: int = 10,
) -> None:
    """Transcribe an audio file and persist transcript text to disk.

    Args:
        source_audio_path: Local input audio file path.
        chunks_output_dir: Directory where intermediate chunk MP3s are written.
        transcript_output_path: Output path for transcript text.
        transcribe_model: Transcription model identifier.
        chunk_length_minutes: Chunk duration in minutes.
    """

    full_transcript = transcribe_audio_to_text(
        source_audio_path=source_audio_path,
        chunks_output_dir=chunks_output_dir,
        transcribe_model=transcribe_model,
        chunk_length_minutes=chunk_length_minutes,
    )

    write_transcript(full_transcript, transcript_output_path)

    print(f"Saved transcript to {transcript_output_path}")
