from abc import ABC

from morse_decoder.pipeline.dto import MorseElement, Transcription
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class Interpreter(ManyToManyStage[MorseElement, Transcription], ABC):
    """Render a stream of decoded elements into corrected, readable text."""
