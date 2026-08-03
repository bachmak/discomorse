from abc import ABC

from morse_decoder.pipeline.dto import ToneSample
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class KeyingDebouncer(ManyToManyStage[ToneSample, ToneSample], ABC):
    """Reports the side of the key that has held long enough to be believed."""
