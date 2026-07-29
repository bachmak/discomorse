import datetime

import numpy as np
import pytest
from audio_fixtures import EPOCH, epoch_clock, sine_pcm

from morse_decoder.audio.impl.resampler import Resampler
from morse_decoder.audio.mic_source import EndOfStream, MicSource
from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.dto import PcmChunk

_TARGET_RATE = 8_000
_SOURCE_RATE = 48_000


class _StubResampler(Resampler):
    """Replays scripted outputs and records what was pushed — no soxr involved."""

    def __init__(self, outputs: list[bytes], tail: bytes = b"") -> None:
        self._outputs = list(outputs)
        self._tail = tail
        self.pushed: list[bytes] = []

    def push(self, chunk: bytes) -> bytes:
        self.pushed.append(chunk)
        return self._outputs.pop(0)

    def flush(self) -> bytes:
        return self._tail


def _mic_source(resampler: Resampler) -> MicSource:
    return MicSource(resampler=resampler, sample_clock=epoch_clock(_TARGET_RATE))


async def _drain(source: MicSource) -> list[PcmChunk]:
    return [chunk async for chunk in source.stream()]


async def _drain_data(source: MicSource) -> list[bytes]:
    return [chunk.data for chunk in await _drain(source)]


@pytest.mark.parametrize(
    ("outputs", "tail", "want"),
    [
        pytest.param([b"AA", b"BB"], b"", [b"AA", b"BB"], id="one-chunk-per-push"),
        pytest.param([b"", b"AA"], b"", [b"AA"], id="withheld-output-skipped"),
        pytest.param([b"AA"], b"TT", [b"AA", b"TT"], id="tail-yielded-last"),
        pytest.param([b"", b""], b"TT", [b"TT"], id="tail-only"),
        pytest.param([b"", b""], b"", [], id="nothing-decodable"),
    ],
)
async def test_mic_source_streams_resampled_chunks(
    outputs: list[bytes], tail: bytes, want: list[bytes]
) -> None:
    source = _mic_source(_StubResampler(outputs, tail))
    for index in range(len(outputs)):
        await source.push(f"raw-{index}".encode())
    await source.push(EndOfStream())

    assert await _drain_data(source) == want


async def test_mic_source_pushes_raw_chunks_into_the_resampler() -> None:
    resampler = _StubResampler([b"", b""])
    source = _mic_source(resampler)

    await source.push(b"raw-0")
    await source.push(b"raw-1")
    await source.push(EndOfStream())
    await _drain(source)

    assert resampler.pushed == [b"raw-0", b"raw-1"]


async def test_mic_source_stops_at_end_of_stream() -> None:
    resampler = _StubResampler([b"AA", b"BB"])
    source = _mic_source(resampler)

    await source.push(b"raw-0")
    await source.push(EndOfStream())
    await source.push(b"raw-1")

    assert await _drain_data(source) == [b"AA"]
    assert resampler.pushed == [b"raw-0"]


async def test_mic_source_timestamps_chunks_by_samples_already_streamed() -> None:
    source = _mic_source(_StubResampler([b"A" * 1600, b"B" * 800], tail=b"T" * 400))
    for index in range(2):
        await source.push(f"raw-{index}".encode())
    await source.push(EndOfStream())

    stamps = [chunk.ts for chunk in await _drain(source)]

    assert stamps == [
        EPOCH,
        EPOCH + datetime.timedelta(seconds=0.1),
        EPOCH + datetime.timedelta(seconds=0.15),
    ]


async def test_mic_source_converts_a_browser_stream_to_the_pipeline_rate() -> None:
    source = _mic_source(Resampler(source_rate=_SOURCE_RATE, target_rate=_TARGET_RATE))
    pcm = sine_pcm(440, 1.0, _SOURCE_RATE).tobytes()
    for offset in range(0, len(pcm), 4096):
        await source.push(pcm[offset : offset + 4096])
    await source.push(EndOfStream())

    samples = np.frombuffer(b"".join(await _drain_data(source)), dtype=PCM16.IntType)

    assert abs(len(samples) - _TARGET_RATE) <= 1
