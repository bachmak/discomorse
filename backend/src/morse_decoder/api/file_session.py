import datetime
from collections.abc import AsyncIterator

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import global_settings
from morse_decoder.pipeline.factory import create_pipeline_runner
from morse_decoder.pipeline.runner import PipelineRunner

_NDJSON_MEDIA_TYPE = "application/x-ndjson"


async def handle_file_upload(file: UploadFile) -> StreamingResponse:
    settings = global_settings
    source = FileSource(
        await file.read(),
        audio=global_settings.audio,
        decoder=SoundFileDecoder(),
        sample_clock=SampleClock(
            sample_rate=settings.audio.sample_rate,
            started_at=datetime.datetime.fromtimestamp(0, tz=datetime.UTC),
        ),
    )
    runner = create_pipeline_runner(source, settings.pipeline)
    return StreamingResponse(FileSession(runner).run(), media_type=_NDJSON_MEDIA_TYPE)


class FileSession:
    """Streams a decoded file's events out as newline-delimited JSON."""

    def __init__(self, runner: PipelineRunner) -> None:
        self._runner = runner

    async def run(self) -> AsyncIterator[str]:
        async for event in self._runner.run():
            yield f"{event.to_message().model_dump_json()}\n"
