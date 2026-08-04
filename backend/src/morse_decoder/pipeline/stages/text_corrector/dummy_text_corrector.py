from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import TextCorrectorSettings
from morse_decoder.pipeline.dto import CorrectedText, Token
from morse_decoder.pipeline.stages.text_corrector.interface import TextCorrector


class DummyTextCorrector(TextCorrector):
    """Placeholder until the real correction moves out of the interpreter."""

    def __init__(self, settings: TextCorrectorSettings) -> None:
        self._settings = settings

    async def process(
        self, tokens: AsyncIterable[Token]
    ) -> AsyncIterator[CorrectedText]:
        async for _ in tokens:
            yield CorrectedText(text="")
