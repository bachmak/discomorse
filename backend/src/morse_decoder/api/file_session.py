import datetime
from collections.abc import AsyncIterator

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import Settings
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline

_NDJSON_MEDIA_TYPE = "application/x-ndjson"


async def handle_file_upload(file: UploadFile) -> StreamingResponse:
    settings = Settings()
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
    """Streams a decoded file's events out as newline-delimited JSON."""

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    async def run(self) -> AsyncIterator[str]:
        async for event in self._pipeline.run():
            yield f"{event.model_dump_json()}\n"
