from abc import ABC

from morse_decoder.pipeline.dto import CarrierSample, ToneSpectrum
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class CarrierSource(ManyToManyStage[ToneSpectrum, CarrierSample], ABC):
    """Follows the carrier every spectrum carries, if it has one."""
