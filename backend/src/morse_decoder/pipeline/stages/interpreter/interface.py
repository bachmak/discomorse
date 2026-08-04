from abc import ABC

from morse_decoder.pipeline.dto import CorrectedText, MorseElement
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class Interpreter(ManyToManyStage[MorseElement, CorrectedText], ABC):
    """Render a stream of decoded elements into corrected, readable text."""
