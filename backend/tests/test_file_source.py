import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import sine_wav

from morse_decoder.audio.file_source import FileSource
from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import AudioSettings

_TARGET_RATE = 8_000


async def _drain(source: FileSource) -> npt.NDArray[PCM16.IntType]:
    chunks = [chunk async for chunk in source.stream()]
    return np.frombuffer(b"".join(chunks), dtype=PCM16.IntType)


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

    samples = await _drain(FileSource(data, audio))

    assert samples.dtype == PCM16.IntType
    # 1 s normalized to the target rate lands near `sample_rate` (polyphase edges)
    assert abs(len(samples) - audio.sample_rate) < 100


@pytest.mark.parametrize("chunk_size", [256, 1024, 4096])
async def test_file_source_chunks_respect_chunk_size(chunk_size: int) -> None:
    audio = AudioSettings(sample_rate=_TARGET_RATE, chunk_size=chunk_size)
    data = sine_wav(freq_hz=440, duration_s=1.0, sample_rate=_TARGET_RATE)

    chunks = [chunk async for chunk in FileSource(data, audio).stream()]

    chunk_bytes = audio.chunk_size * PCM16.BYTES_PER_SAMPLE
    assert all(len(chunk) == chunk_bytes for chunk in chunks[:-1])
    assert all(len(chunk) <= chunk_bytes for chunk in chunks)
