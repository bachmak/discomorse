from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import TimingReading, Transcription
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter


class DummyInterpreter(Interpreter):
    """Stand-in until real interpretation lands: transcribes nothing."""

    def __init__(self, settings: InterpreterSettings) -> None:
        self._settings = settings

    async def interpret(self, reading: TimingReading) -> Transcription:
        return Transcription(text="")
