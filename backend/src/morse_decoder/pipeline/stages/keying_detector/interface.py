from abc import ABC

from morse_decoder.pipeline.dto import CarrierNoiseSample, DigitalTone
from morse_decoder.pipeline.stages.interface import OneToOneStage


class KeyingDetector(OneToOneStage[CarrierNoiseSample, DigitalTone], ABC):
    """Tells whether the carrier stands above the noise as a keyed tone."""
