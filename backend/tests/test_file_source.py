import datetime

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import EPOCH, epoch_clock, sine_wav

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.impl.decoder import SoundFileDecoder
from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import AudioSettings
from morse_decoder.pipeline.dto import PcmChunk

_TARGET_RATE = 8_000


def _file_source(data: bytes, audio: AudioSettings) -> FileSource:
    return FileSource(
        data,
        audio=audio,
        decoder=SoundFileDecoder(),
        sample_clock=epoch_clock(audio.sample_rate),
    )


async def _drain(source: FileSource) -> list[PcmChunk]:
    return [chunk async for chunk in source.stream()]


async def _drain_samples(source: FileSource) -> npt.NDArray[PCM16.IntType]:
    chunks = await _drain(source)
    return np.frombuffer(b"".join(chunk.data for chunk in chunks), dtype=PCM16.IntType)


@pytest.mark.parametrize(
    ("source_rate", "channels"),
    [
        pytest.param(_TARGET_RATE, 1, id="passthrough"),
        pytest.param(16_000, 1, id="downsample"),
        pytest.param(4_000, 1, id="upsample"),
        pytest.param(_TARGET_RATE, 2, id="downmix-stereo"),
        pytest.param(16_000, 2, id="downsample-and-downmix"),
    ],
)
async def test_file_source_normalizes_to_mono_int16_target_rate(
    source_rate: int, channels: int
) -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=2048)
    data = sine_wav(
        freq_hz=440, duration_s=1.0, sample_rate=source_rate, channels=channels
    )

    samples = await _drain_samples(_file_source(data, audio))

    assert samples.dtype == PCM16.IntType
    # 1 s normalized to the target rate lands near `sample_rate` (polyphase edges)
    assert abs(len(samples) - audio.sample_rate) < 100


@pytest.mark.parametrize("chunk_size", [256, 1024, 4096])
async def test_file_source_chunks_respect_chunk_size(chunk_size: int) -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=chunk_size)
    data = sine_wav(freq_hz=440, duration_s=1.0, sample_rate=_TARGET_RATE)

    chunks = await _drain(_file_source(data, audio))

    chunk_bytes = audio.chunk_size * PCM16.BYTES_PER_SAMPLE
    assert all(len(chunk.data) == chunk_bytes for chunk in chunks[:-1])
    assert all(len(chunk.data) <= chunk_bytes for chunk in chunks)


async def test_file_source_timestamps_chunks_at_their_playback_offset() -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=1024)
    data = sine_wav(freq_hz=440, duration_s=1.0, sample_rate=_TARGET_RATE)

    stamps = [chunk.ts for chunk in await _drain(_file_source(data, audio))]

    step = datetime.timedelta(seconds=audio.chunk_size / audio.sample_rate)
    assert stamps == [EPOCH + index * step for index in range(len(stamps))]
