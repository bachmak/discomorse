from morse_decoder.pipeline.dto import CarrierSample, ToneSpectrum
from morse_decoder.pipeline.stages.interface import PipelineStage


class CarrierSource(PipelineStage[ToneSpectrum, CarrierSample]):
    """Follows the carrier every spectrum carries, if it has one."""
