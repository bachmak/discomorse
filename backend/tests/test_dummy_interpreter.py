import pytest
from stream_fixtures import stream

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    MorseElement,
    Transcription,
    WordSpace,
)
from morse_decoder.pipeline.stages.interpreter.dummy_interpreter import DummyInterpreter


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([], [], id="empty"),
        pytest.param([Dit()], [Transcription(text="")], id="one-element"),
        pytest.param(
            [Dit(), Dah(), WordSpace()],
            [Transcription(text="")] * 3,
            id="several-elements",
        ),
    ],
)
async def test_process_reads_every_element_and_transcribes_nothing(
    elements: list[MorseElement], want: list[Transcription]
) -> None:
    interpreter = DummyInterpreter(InterpreterSettings())

    transcriptions = interpreter.process(stream(*elements))

    assert [transcription async for transcription in transcriptions] == want
