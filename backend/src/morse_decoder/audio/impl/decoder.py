import io
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
import soundfile as sf  # type: ignore[import-untyped]  # no stubs


@dataclass(frozen=True)
class DecodedAudio:
    """Float32 PCM in [-1, 1], shaped (frames, channels), at the native rate."""

    samples: npt.NDArray[np.float32]
    sample_rate: int


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
