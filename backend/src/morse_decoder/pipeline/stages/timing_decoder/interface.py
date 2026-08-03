from abc import ABC

from morse_decoder.pipeline.dto import MorseElement, ToneSample
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class TimingDecoder(ManyToManyStage[ToneSample, MorseElement], ABC):
    """Decode a stream of tone samples into morse timing elements."""
