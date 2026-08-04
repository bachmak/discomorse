"""Runs a local audio file through the pipeline and prints what it decoded.

Debugging aid: the production pipeline minus the frontend and the HTTP layer.

    python3 decode_file.py <path-to-file>
"""

import argparse
import asyncio
import datetime
from collections.abc import Sequence
from pathlib import Path

from morse_decoder.api.messages import (
    ChannelName,
    StreamMessage,
    TextMessage,
)
from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import PipelineSettings, Settings, StreamSettings
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline

_EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.UTC)


class Excerpt:
    """One labelled line of the report, fed by the channel it listens to."""

    def __init__(self, label: str, channel: ChannelName) -> None:
        self._label = label
        self._channel = channel
        self._parts: list[str] = []

    def absorb(self, message: StreamMessage) -> None:
        self._parts.extend(self._fragments(message))

    def text(self) -> str:
        """Everything this excerpt collected, unlabelled."""
        return "".join(self._parts)

    def render(self) -> str:
        return f"{self._label}: {self.text()}"

    def _fragments(self, message: StreamMessage) -> tuple[str, ...]:
        """What this excerpt reads off the message; empty when it isn't its business."""
        if message.channel != self._channel:
            return ()
        payload = message.payload
        return (payload.data,) if isinstance(payload, TextMessage) else ()


class Report:
    """What a run is worth printing, one line per excerpt."""

    def __init__(self, excerpts: Sequence[Excerpt]) -> None:
        self._excerpts = excerpts

    def absorb(self, message: StreamMessage) -> None:
        for excerpt in self._excerpts:
            excerpt.absorb(message)

    def render(self) -> str:
        return "\n".join(excerpt.render() for excerpt in self._excerpts)


class FileDecoding:
    """One pass: file on disk → source → pipeline → filled report."""

    def __init__(self, path: Path, settings: Settings, report: Report) -> None:
        self._path = path
        self._settings = settings
        self._report = report

    async def run(self) -> Report:
        async for message in self._pipeline().run():
            self._report.absorb(message)
        return self._report

    def _pipeline(self) -> Pipeline:
        return create_pipeline(self._source(), self._settings.pipeline)

    def _source(self) -> FileSource:
        return FileSource(
            self._path.read_bytes(),
            audio=self._settings.audio,
            decoder=SoundFileDecoder(),
            sample_clock=SampleClock(self._settings.audio.sample_rate, _EPOCH),
        )


def _parse_path() -> Path:
    parser = argparse.ArgumentParser(
        description="Decode a local audio file with the morse pipeline."
    )
    parser.add_argument("audio_file", type=Path, help="wav/flac/ogg/mp3 to decode")
    path = Path(parser.parse_args().audio_file)
    if not path.is_file():
        parser.error(f"no such file: {path}")
    return path


def _settings() -> Settings:
    return Settings(
        pipeline=PipelineSettings(
            stream_settings=StreamSettings(
                morse_elements=True,
                corrected_text=True,
            )
        )
    )


def main() -> None:
    report = Report(
        (Excerpt("morse", "morse_elements"), Excerpt("text", "corrected_text"))
    )
    decoding = FileDecoding(_parse_path(), _settings(), report)
    print(asyncio.run(decoding.run()).render())


if __name__ == "__main__":
    main()
