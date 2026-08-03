from abc import ABC

from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.interface import OneToOneStage


class SpectrumLimiter(OneToOneStage[ToneSpectrum, ToneSpectrum], ABC):
    """Cuts every spectrum down to the bins worth reading a carrier off."""
