from morse_decoder.pipeline.dto import CarrierNoiseSample, ToneSample
from morse_decoder.pipeline.stages.interface import PipelineStage


class KeyingDetector(PipelineStage[CarrierNoiseSample, ToneSample]):
    """Tells whether the carrier stands above the noise as a keyed tone."""
