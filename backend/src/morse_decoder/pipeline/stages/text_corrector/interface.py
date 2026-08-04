from abc import ABC

from morse_decoder.pipeline.dto import CorrectedText, Token
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class TextCorrector(ManyToManyStage[Token, CorrectedText], ABC):
    """Render a stream of decoded tokens into corrected, readable text."""
