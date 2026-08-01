from morse_decoder.pipeline.dto import ToneSample
from morse_decoder.pipeline.stages.interface import PipelineStage


class KeyingDebouncer(PipelineStage[ToneSample, ToneSample]):
    """Reports the side of the key that has held long enough to be believed."""
