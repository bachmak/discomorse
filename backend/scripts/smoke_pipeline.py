"""Smoke test: drives a generated morse WAV through the whole pipeline.

Fails when a stage raises or when the pipeline stops emitting the messages the
frontend lives on. The web API is deliberately out of scope.
"""

import asyncio
import datetime
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from morse_signal import MorseSignal

from morse_decoder.api.messages import (
    OutboundMessage,
    TextMessage,
    ToneSpectrumMessage,
)
from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import PipelineSettings, Settings, StreamSettings
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline

_MESSAGE = "SOS DE SMOKE TEST"
_EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.UTC)
_EXPECTED: tuple[type[OutboundMessage], ...] = (
    ToneSpectrumMessage,
    TextMessage,
)


@dataclass(frozen=True)
class MessageTally:
    """How many messages of each kind one pipeline run emitted."""

    counts: Counter[type[OutboundMessage]]

    def missing(self, expected: Iterable[type[OutboundMessage]]) -> tuple[str, ...]:
        return tuple(kind.__name__ for kind in expected if not self.counts[kind])

    def report(self) -> str:
        lines = sorted(f"  {kind.__name__}: {n}" for kind, n in self.counts.items())
        return "\n".join(["messages:", *lines])


class SmokeRun:
    """One pass: file on disk → source → pipeline → serialized wire messages."""

    def __init__(self, path: Path, settings: Settings) -> None:
        self._path = path
        self._settings = settings

    async def tally(self) -> MessageTally:
        counts: Counter[type[OutboundMessage]] = Counter()
        async for message in self._pipeline().run():
            message.model_dump_json()  # serialization is under test too
            counts[type(message.payload)] += 1
        return MessageTally(counts)

    def _pipeline(self) -> Pipeline:
        return create_pipeline(self._source(), self._settings.pipeline)

    def _source(self) -> FileSource:
        return FileSource(
            self._path.read_bytes(),
            audio=self._settings.audio,
            decoder=SoundFileDecoder(),
            sample_clock=SampleClock(self._settings.audio.sample_rate, _EPOCH),
        )


def _write_signal(directory: Path, settings: Settings) -> Path:
    path = directory / "smoke.wav"
    path.write_bytes(MorseSignal(settings.audio.sample_rate).wav(_MESSAGE))
    return path


def _run(settings: Settings) -> MessageTally:
    with TemporaryDirectory() as directory:
        path = _write_signal(Path(directory), settings)
        return asyncio.run(SmokeRun(path, settings).tally())


def _settings() -> Settings:
    return Settings(
        pipeline=PipelineSettings(
            stream_settings=StreamSettings(
                spectrums=True,
                limited_spectrums=True,
                carrier_samples=True,
                noise_samples=True,
                raw_tones=True,
                debounced_tones=True,
                morse_elements=True,
                decoded_symbols=True,
                corrected_text=True,
            )
        )
    )


def main() -> int:
    tally = _run(_settings())
    print(tally.report())
    missing = tally.missing(_EXPECTED)
    if missing:
        print(f"pipeline emitted no {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
