from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import Mark, MorseElement, Transcription
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter


class DummyInterpreter(Interpreter):
    """Stand-in until real interpretation lands: transcribes nothing."""

    def __init__(self, settings: InterpreterSettings) -> None:
        self._settings = settings

    async def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Transcription]:
        async for element in elements:
            if isinstance(element, Mark):
                yield Transcription(text=element.notation())
