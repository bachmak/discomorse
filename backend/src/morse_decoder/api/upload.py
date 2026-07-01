from collections.abc import AsyncIterator

from fastapi import UploadFile
from fastapi.responses import StreamingResponse

from morse_decoder.audio.file_source import FileSource
from morse_decoder.config import settings
from morse_decoder.pipeline.factory import create_pipeline_runner
from morse_decoder.pipeline.runner import PipelineRunner

_NDJSON_MEDIA_TYPE = "application/x-ndjson"


async def handle_file_upload(file: UploadFile) -> StreamingResponse:
    source = FileSource(await file.read(), settings.audio)
    runner = create_pipeline_runner(source, settings.pipeline)
    return StreamingResponse(
        FileUploadSession(runner).stream(), media_type=_NDJSON_MEDIA_TYPE
    )


class FileUploadSession:
    """Streams a decoded file's events out as newline-delimited JSON."""

    def __init__(self, runner: PipelineRunner) -> None:
        self._runner = runner

    async def stream(self) -> AsyncIterator[str]:
        async for event in self._runner.run():
            yield f"{event.to_message().model_dump_json()}\n"
