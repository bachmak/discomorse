"""Smoke test: drives a generated morse WAV through the whole pipeline.

Fails when a stage raises or when the runner stops emitting the events the
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

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.config import Settings, global_settings
from morse_decoder.pipeline.events import FFTFrame, OutboundEvent, WaterfallFrame
from morse_decoder.pipeline.factory import create_pipeline_runner
from morse_decoder.pipeline.runner import PipelineRunner

_MESSAGE = "SOS DE SMOKE TEST"
_EPOCH = datetime.datetime.fromtimestamp(0, tz=datetime.UTC)
_EXPECTED: tuple[type[OutboundEvent], ...] = (WaterfallFrame, FFTFrame)


@dataclass(frozen=True)
class EventTally:
    """How many events of each kind one pipeline run emitted."""

    counts: Counter[type[OutboundEvent]]

    def missing(self, expected: Iterable[type[OutboundEvent]]) -> tuple[str, ...]:
        return tuple(kind.__name__ for kind in expected if not self.counts[kind])

    def report(self) -> str:
        lines = sorted(f"  {kind.__name__}: {n}" for kind, n in self.counts.items())
        return "\n".join(["events:", *lines])


class SmokeRun:
    """One pass: file on disk → source → pipeline → serialized wire messages."""

    def __init__(self, path: Path, settings: Settings) -> None:
        self._path = path
        self._settings = settings

    async def tally(self) -> EventTally:
        counts: Counter[type[OutboundEvent]] = Counter()
        async for event in self._runner().run():
            event.to_message().model_dump_json()  # serialization is under test too
            counts[type(event)] += 1
        return EventTally(counts)

    def _runner(self) -> PipelineRunner:
        return create_pipeline_runner(self._source(), self._settings.pipeline)

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


def _run(settings: Settings) -> EventTally:
    with TemporaryDirectory() as directory:
        path = _write_signal(Path(directory), settings)
        return asyncio.run(SmokeRun(path, settings).tally())


def main() -> int:
    tally = _run(global_settings)
    print(tally.report())
    missing = tally.missing(_EXPECTED)
    if missing:
        print(f"pipeline emitted no {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
