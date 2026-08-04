from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import SymbolDecoderSettings
from morse_decoder.pipeline.dto import MorseElement, Token
from morse_decoder.pipeline.stages.symbol_decoder.interface import SymbolDecoder


class DummySymbolDecoder(SymbolDecoder):
    """Placeholder until the real decoding moves out of the interpreter."""

    def __init__(self, settings: SymbolDecoderSettings) -> None:
        self._settings = settings

    async def process(self, items: AsyncIterable[MorseElement]) -> AsyncIterator[Token]:
        async for _ in items:
            yield Token(value="")
