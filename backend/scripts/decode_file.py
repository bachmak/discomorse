"""Runs a local audio file through the pipeline and prints what it decoded.

Debugging aid: the production pipeline minus the frontend and the HTTP layer.

    python3 decode_file.py <path-to-file>
"""

import argparse
import asyncio
import datetime
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import Settings, global_settings
from morse_decoder.pipeline.events import DecodedMorse, DecodedText, OutboundEvent
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline

_EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.UTC)


class Excerpt(ABC):
    """One labelled line of the report, fed by the events it recognizes."""

    def __init__(self) -> None:
        self._parts: list[str] = []

    def absorb(self, event: OutboundEvent) -> None:
        self._parts.extend(self._fragments(event))

    def text(self) -> str:
        """Everything this excerpt collected, unlabelled."""
        return "".join(self._parts)

    def render(self) -> str:
        return f"{self._label}: {self.text()}"

    @property
    @abstractmethod
    def _label(self) -> str: ...

    @abstractmethod
    def _fragments(self, event: OutboundEvent) -> tuple[str, ...]:
        """What this excerpt reads off the event; empty when it isn't its business."""
        ...


class MorseExcerpt(Excerpt):
    """The dits, dahs and spaces the timing decoder emitted."""

    @property
    def _label(self) -> str:
        return "morse"

    def _fragments(self, event: OutboundEvent) -> tuple[str, ...]:
        return (event.element.notation,) if isinstance(event, DecodedMorse) else ()


class TextExcerpt(Excerpt):
    """The text the interpreter made of those elements."""

    @property
    def _label(self) -> str:
        return "text"

    def _fragments(self, event: OutboundEvent) -> tuple[str, ...]:
        return (event.text,) if isinstance(event, DecodedText) else ()


class Report:
    """What a run is worth printing, one line per excerpt."""

    def __init__(self, excerpts: Sequence[Excerpt]) -> None:
        self._excerpts = excerpts

    def absorb(self, event: OutboundEvent) -> None:
        for excerpt in self._excerpts:
            excerpt.absorb(event)

    def render(self) -> str:
        return "\n".join(excerpt.render() for excerpt in self._excerpts)


class FileDecoding:
    """One pass: file on disk → source → pipeline → filled report."""

    def __init__(self, path: Path, settings: Settings, report: Report) -> None:
        self._path = path
        self._settings = settings
        self._report = report

    async def run(self) -> Report:
        async for event in self._pipeline().run():
            self._report.absorb(event)
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


def main() -> None:
    report = Report((MorseExcerpt(), TextExcerpt()))
    decoding = FileDecoding(_parse_path(), global_settings, report)
    print(asyncio.run(decoding.run()).render())


if __name__ == "__main__":
    main()
