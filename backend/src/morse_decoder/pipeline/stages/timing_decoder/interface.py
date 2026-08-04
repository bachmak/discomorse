from abc import ABC

from morse_decoder.pipeline.dto import DigitalTone, MorseElement
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class TimingDecoder(ManyToManyStage[DigitalTone, MorseElement], ABC):
    """Decode a stream of tone samples into morse timing elements."""
