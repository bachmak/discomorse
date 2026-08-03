from abc import ABC

from morse_decoder.pipeline.dto import NoiseSample, ToneSpectrum
from morse_decoder.pipeline.stages.interface import OneToOneStage


class NoiseEstimator(OneToOneStage[ToneSpectrum, NoiseSample], ABC):
    """Reads the noise floor every spectrum sits on."""
