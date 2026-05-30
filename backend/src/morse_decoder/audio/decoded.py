from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class DecodedAudio:
    """Float32 PCM in [-1, 1], shaped (frames, channels), at the native rate."""

    samples: npt.NDArray[np.float32]
    sample_rate: int
