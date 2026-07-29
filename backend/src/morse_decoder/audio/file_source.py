from collections.abc import AsyncIterator

from morse_decoder.audio.impl.decoder import AudioDecoder
from morse_decoder.audio.impl.pcm_normalizer import PcmNormalizer
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.audio.source import AudioSource
from morse_decoder.config import AudioSettings
from morse_decoder.pipeline.dto import PcmChunk


class FileSource(AudioSource):
    """Decodes an uploaded audio file and streams Int16 PCM chunks."""

    def __init__(
        self,
        data: bytes,
        audio: AudioSettings,
        decoder: AudioDecoder,
        sample_clock: SampleClock,
    ) -> None:
        normalizer = PcmNormalizer(audio.sample_rate)

        decoded = decoder.decode(data)
        normalized = normalizer.normalize(decoded)

        self._raw = normalized
        self._chunk = audio.chunk_size * PCM16.BYTES_PER_SAMPLE
        self._sample_clock = sample_clock

    async def stream(self) -> AsyncIterator[PcmChunk]:
        for i in range(0, len(self._raw), self._chunk):
            chunk = self._raw[i : i + self._chunk]
            yield self._sample_clock.stamp(chunk)
