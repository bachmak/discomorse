from collections.abc import AsyncIterator

import pytest
from stream_fixtures import stream

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    MorseElement,
    Transcription,
    WordGap,
)
from morse_decoder.pipeline.stages.interpreter.dummy_interpreter import DummyInterpreter

_ELEMENTS: list[MorseElement] = [Dit(), Dah(), WordGap()]


def _interpreter() -> DummyInterpreter:
    return DummyInterpreter(InterpreterSettings())


async def _counted(
    elements: list[MorseElement], read: list[MorseElement]
) -> AsyncIterator[MorseElement]:
    """The elements handed over, written down as they are drawn."""
    for element in elements:
        read.append(element)
        yield element


@pytest.mark.parametrize(
    "elements, want",
    [
        pytest.param([], [], id="nothing-at-all"),
        pytest.param([Dit()], [Transcription(text=".")], id="one-signal"),
        pytest.param([WordGap()], [], id="one-space"),
        pytest.param(
            _ELEMENTS,
            [Transcription(text="."), Transcription(text="-")],
            id="several-elements",
        ),
    ],
)
async def test_process_transcribes_every_signal_it_is_handed(
    elements: list[MorseElement],
    want: list[Transcription],
) -> None:
    transcriptions = _interpreter().process(stream(*elements))

    assert [transcription async for transcription in transcriptions] == want


async def test_process_reads_every_element_it_is_handed() -> None:
    """Nothing else draws on the decoder, so a stage it starves never runs."""
    read: list[MorseElement] = []

    async for _ in _interpreter().process(_counted(_ELEMENTS, read)):
        pass

    assert read == _ELEMENTS
