from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.interface import PipelineStage


class SpectrumLimiter(PipelineStage[ToneSpectrum, ToneSpectrum]):
    """Cuts every spectrum down to the bins worth reading a carrier off."""
