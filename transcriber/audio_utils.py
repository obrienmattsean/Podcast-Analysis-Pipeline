"""Utilities for downloading podcast audio files to local storage."""

from pathlib import Path
from urllib.request import urlopen


def download_audio_file(audio_url: str, output_path: Path, timeout_seconds: int = 60) -> Path:
    """Download an audio file from an HTTP URL to a local path.

    Args:
        audio_url: Source HTTP(S) URL that serves the audio bytes.
        output_path: Local file path where the downloaded audio is written.
        timeout_seconds: Network timeout in seconds for opening the URL.

    Returns:
        Path: The same output path after a successful download.

    Example:
        >>> from pathlib import Path
        >>> path = download_audio_file(
        ...     "https://example.com/episode.mp3",
        ...     Path("/tmp/episode.mp3"),
        ... )
        >>> path.name
        'episode.mp3'
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with (
        urlopen(audio_url, timeout=timeout_seconds) as response,
        output_path.open("wb") as out_file,
    ):
        out_file.write(response.read())

    return output_path
