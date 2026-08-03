from abc import ABC

from morse_decoder.pipeline.dto import CarrierNoiseSample, ToneSample
from morse_decoder.pipeline.stages.interface import OneToOneStage


class KeyingDetector(OneToOneStage[CarrierNoiseSample, ToneSample], ABC):
    """Tells whether the carrier stands above the noise as a keyed tone."""
