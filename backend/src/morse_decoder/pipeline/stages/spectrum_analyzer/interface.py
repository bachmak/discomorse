from abc import ABC

from morse_decoder.pipeline.dto import PcmChunk, ToneSpectrum
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class SpectrumAnalyzer(ManyToManyStage[PcmChunk, ToneSpectrum], ABC):
    """Turn a stream of PCM chunks into a stream of frequency spectrums."""
