from abc import ABC

from morse_decoder.pipeline.dto import MorseElement, Token
from morse_decoder.pipeline.stages.interface import ManyToManyStage


class SymbolDecoder(ManyToManyStage[MorseElement, Token], ABC):
    """Decode a stream of morse timing elements into the tokens they spell."""
