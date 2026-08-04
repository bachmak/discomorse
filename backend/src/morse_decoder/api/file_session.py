import datetime
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import Json

from morse_decoder.api.helpers import subscription_to_settings
from morse_decoder.api.messages import SubscriptionMessage
from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import PipelineSettings, Settings
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline

_NDJSON_MEDIA_TYPE = "application/x-ndjson"


async def handle_file_upload(
    file: UploadFile,
    subscription: Annotated[Json[SubscriptionMessage], Form()],
) -> StreamingResponse:
    stream_settings = subscription_to_settings(subscription)
    settings = Settings(pipeline=PipelineSettings(stream_settings=stream_settings))
    source = FileSource(
        await file.read(),
        audio=settings.audio,
        decoder=SoundFileDecoder(),
        sample_clock=SampleClock(
            sample_rate=settings.audio.sample_rate,
            started_at=datetime.datetime.fromtimestamp(0, tz=datetime.UTC),
        ),
    )
    pipeline = create_pipeline(source, settings.pipeline)
    return StreamingResponse(FileSession(pipeline).run(), media_type=_NDJSON_MEDIA_TYPE)


class FileSession:
    """Streams a decoded file's messages out as newline-delimited JSON."""

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    async def run(self) -> AsyncIterator[str]:
        async for message in self._pipeline.run():
            yield f"{message.model_dump_json()}\n"
