from typing import TypeAlias

import numpy as np


class PCM16:
    BYTES_PER_SAMPLE = 2
    FULL_SCALE = 32768.0
    INT_PEAK = 32767

    IntType: TypeAlias = np.int16  # noqa: UP040
    FloatType: TypeAlias = np.float32  # noqa: UP040

    IntTypeStr = "int16"
    WavSubtype = "PCM_16"
