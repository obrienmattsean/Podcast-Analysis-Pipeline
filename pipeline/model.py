from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator


class ValidatedEpisode(BaseModel):
    model_config = ConfigDict(extra="ignore")
    podcast_id: int
    title: str
    audio_link: HttpUrl
    published_at: datetime
    summary: Optional[str] = None
    transcribed: bool = False

    @field_validator("audio_link")
    @classmethod
    def validate_audio_link(cls, value: HttpUrl) -> HttpUrl:
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
                "audio_link must point to an audio file "
                f"({', '.join(allowed_extensions)})"
            )
        return value
