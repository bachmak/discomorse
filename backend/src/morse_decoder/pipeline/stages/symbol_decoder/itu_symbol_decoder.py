from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import SymbolDecoderSettings
from morse_decoder.pipeline.dto import MorseElement, Token
from morse_decoder.pipeline.stages.symbol_decoder.impl.code_reader import ItuCodeReader
from morse_decoder.pipeline.stages.symbol_decoder.impl.morse_normalizer import (
    MorseNormalizer,
)
from morse_decoder.pipeline.stages.symbol_decoder.interface import SymbolDecoder


class ItuSymbolDecoder(SymbolDecoder):
    """Gathers loose elements into whole codes and reads each off the ITU table.

    Deterministic and stateless beyond the character it is part way through:
    the same elements always spell the same tokens. Nothing here weighs what
    the message is likely to say, which is the correcting stage's business.
    """

    def __init__(self, settings: SymbolDecoderSettings) -> None:
        self._normalizer = MorseNormalizer()
        self._reader = ItuCodeReader()

    async def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Token]:
        async for symbol in self._normalizer.process(elements):
            yield Token(value=self._reader.read(symbol).text())
