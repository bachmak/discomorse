from collections.abc import AsyncIterator

from morse_decoder.audio.base import AudioSource
from morse_decoder.audio.decoder import AudioDecoder, SoundFileDecoder
from morse_decoder.audio.pcm_normalizer import PcmNormalizer
from morse_decoder.config import AudioSettings

_BYTES_PER_SAMPLE = 2  # Int16


class FileSource(AudioSource):
    """Decodes an uploaded audio file and streams Int16 PCM chunks."""

    def __init__(
        self,
        data: bytes,
        audio: AudioSettings,
        decoder: AudioDecoder | None = None,
    ) -> None:
        decoder = decoder or SoundFileDecoder()
        normalizer = PcmNormalizer(audio.sample_rate)

        decoded = decoder.decode(data)
        normalized = normalizer.normalize(decoded)

        self._raw = normalized
        self._chunk = audio.chunk_size * _BYTES_PER_SAMPLE

    async def stream(self) -> AsyncIterator[bytes]:
        for i in range(0, len(self._raw), self._chunk):
            yield self._raw[i : i + self._chunk]
