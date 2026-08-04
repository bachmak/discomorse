import pytest
from morse_element_fixtures import words
from stream_fixtures import stream

from morse_decoder.config import InterpreterSettings, PipelineSettings
from morse_decoder.pipeline.dto import MorseElement, Transcription
from morse_decoder.pipeline.factory import _build_interpreter
from morse_decoder.pipeline.stages.interpreter.normalizing_interpreter import (
    NormalizingInterpreter,
)

_HI_MY = words(("....", ".."), ("--", "-.--"))


async def _transcribe(elements: list[MorseElement]) -> str:
    interpreter = NormalizingInterpreter(InterpreterSettings())
    return "".join(
        [
            transcription.text
            async for transcription in interpreter.process(stream(*elements))
        ]
    )


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([], "", id="empty"),
        pytest.param(_HI_MY, ".... .. / -- -.--", id="hi-my"),
    ],
)
async def test_process_publishes_the_normalized_notation(
    elements: list[MorseElement], want: str
) -> None:
    assert await _transcribe(elements) == want


async def test_process_transcribes_one_symbol_at_a_time() -> None:
    interpreter = NormalizingInterpreter(InterpreterSettings())

    transcriptions = interpreter.process(stream(*_HI_MY))

    assert [text async for text in transcriptions][:3] == [
        Transcription(text="...."),
        Transcription(text=" .."),
        Transcription(text=" /"),
    ]


def test_factory_builds_registered_interpreter() -> None:
    assert isinstance(_build_interpreter(PipelineSettings()), NormalizingInterpreter)
