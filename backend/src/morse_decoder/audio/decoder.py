import io
from abc import ABC, abstractmethod

import soundfile as sf  # type: ignore[import-untyped]  # no stubs

from morse_decoder.audio.decoded import DecodedAudio


class AudioDecoder(ABC):
    @abstractmethod
    def decode(self, data: bytes) -> DecodedAudio:
        """Decode encoded audio bytes into float samples at their native rate."""
        ...


class SoundFileDecoder(AudioDecoder):
    """Decodes any libsndfile-supported container (wav/flac/ogg/mp3) via soundfile."""

    def decode(self, data: bytes) -> DecodedAudio:
        samples, rate = sf.read(io.BytesIO(data), dtype="float32", always_2d=True)
        return DecodedAudio(samples=samples, sample_rate=int(rate))
