from pydantic import BaseModel, ConfigDict, HttpUrl, PastDatetime, field_validator


class ValidatedEpisode(BaseModel):
    """Validated podcast episode payload.

    Attributes:
        podcast_id (int): Podcast identifier.
        title (str): Episode title.
        audio_link (HttpUrl): Audio URL for the episode.
        published_at (datetime): Episode publication timestamp.
    """

    model_config = ConfigDict(extra="ignore")
    podcast_id: int
    title: str
    audio_link: HttpUrl
    published_at: PastDatetime

    @field_validator("audio_link")
    @classmethod
    def validate_audio_link(cls, value: HttpUrl) -> HttpUrl:
        """Validate that the audio URL ends with an allowed media extension.

        Args:
            value (HttpUrl): Audio URL to validate.

        Returns:
            HttpUrl: The original validated URL.

        Raises:
            ValueError: If the URL does not end with an allowed extension.
        """

        url = str(value).lower()

        allowed_extensions = (
            ".mp3",
            ".m4a",
            ".wav",
            ".aac",
            ".ogg",
            ".flac",
        )

        if not any(url.endswith(ext) for ext in allowed_extensions):
            raise ValueError(
                f"audio_link must point to an audio file ({', '.join(allowed_extensions)})"
            )
        return value
