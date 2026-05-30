import numpy as np
import numpy.typing as npt
from audio_fixtures import sine_wav

from morse_decoder.audio.file_source import FileSource
from morse_decoder.config import AudioSettings


async def _drain(source: FileSource) -> npt.NDArray[np.int16]:
    chunks = [chunk async for chunk in source.stream()]
    return np.frombuffer(b"".join(chunks), dtype=np.int16)


async def test_file_source_resamples_to_target_rate() -> None:
    audio = AudioSettings(sample_rate=8_000, chunk_size=2048)
    data = sine_wav(freq_hz=440, duration_s=1.0, sample_rate=16_000)

    samples = await _drain(FileSource(data, audio))

    # 1 s downsampled 16 kHz -> 8 kHz lands near 8000 samples (polyphase edges)
    assert abs(len(samples) - audio.sample_rate) < 100


async def test_file_source_downmixes_stereo_to_mono() -> None:
    audio = AudioSettings(sample_rate=8_000, chunk_size=2048)
    data = sine_wav(freq_hz=440, duration_s=1.0, sample_rate=8_000, channels=2)

    samples = await _drain(FileSource(data, audio))

    assert samples.dtype == np.int16
    assert abs(len(samples) - audio.sample_rate) < 100


async def test_file_source_chunks_respect_chunk_size() -> None:
    audio = AudioSettings(sample_rate=8_000, chunk_size=1024)
    data = sine_wav(freq_hz=440, duration_s=1.0, sample_rate=8_000)

    chunks = [chunk async for chunk in FileSource(data, audio).stream()]

    chunk_bytes = audio.chunk_size * 2
    assert all(len(chunk) == chunk_bytes for chunk in chunks[:-1])
    assert all(len(chunk) <= chunk_bytes for chunk in chunks)
