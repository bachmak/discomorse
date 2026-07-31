from morse_decoder.pipeline.dto import NoiseSample, ToneSpectrum
from morse_decoder.pipeline.stages.interface import PipelineStage


class NoiseEstimator(PipelineStage[ToneSpectrum, NoiseSample]):
    """Reads the noise floor every spectrum sits on."""
