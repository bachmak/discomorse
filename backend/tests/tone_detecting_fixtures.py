"""Tone detecting: the four stages that turn spectrums into a keyed line.

Carrier source, noise estimator, keying detector and debouncer only meet in the
pipeline, so a test that wants them together drives a real one — the wiring
under test is then the wiring that runs in production, not a copy of it.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass

import numpy.typing as npt
from carrier_fixtures import ANALYZER_SETTINGS
from keying_fixtures import key_off, keys
from spectrum_fixtures import spectrums_of
from tone_fixtures import PcmChunks, flags

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.audio.source import AudioSource
from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.dto import (
    PcmChunk,
    ToneSample,
    ToneSpectrum,
)
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline

SETTINGS = PipelineSettings(spectrum_analyzer_settings=ANALYZER_SETTINGS)


class NoAudio(AudioSource):
    """A source the tone tests never draw from: they feed the stages by hand."""

    async def stream(self) -> AsyncIterator[PcmChunk]:
        return
        yield  # pragma: no cover  # marks stream() a generator, nothing is drawn


class ToneDetecting:
    """One pipeline, read at the point where its keying stages have had their say."""

    def __init__(self, pipeline: Pipeline) -> None:
        self._pipeline = pipeline

    def read(self, spectrums: tuple[ToneSpectrum, ...]) -> tuple[ToneSample, ...]:
        return tuple(self._pipeline._sample(spectrum) for spectrum in spectrums)

    async def feed(self, chunk: PcmChunk) -> tuple[ToneSample, ...]:
        """One chunk of audio, driven through the pipeline the way ``run`` does."""
        return self.read(await spectrums_of(self._pipeline._spectrum_analyzer, chunk))

    def stage[StageT](self, name: str, kind: type[StageT]) -> StageT:
        """The stage the pipeline built under ``name``, told to be a ``kind``."""
        stage = getattr(self._pipeline, f"_{name}")
        assert isinstance(stage, kind)
        return stage


def tone_detecting(settings: PipelineSettings | None = None) -> ToneDetecting:
    return ToneDetecting(create_pipeline(NoAudio(), settings or SETTINGS))


def detect(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    detecting: ToneDetecting | None = None,
) -> tuple[ToneSample, ...]:
    """Feed ``spectrums`` to one set of stages the way the pipeline would."""
    return (detecting or tone_detecting()).read(spectrums)


async def read_tone(
    samples: npt.NDArray[PCM16.IntType], chunks: int = 1
) -> tuple[ToneSample, ...]:
    """The key one set of stages reads off ``samples`` handed to it in ``chunks``."""
    detecting = tone_detecting()
    read: list[ToneSample] = []
    for chunk in PcmChunks(samples, chunks):
        read += await detecting.feed(chunk)
    return tuple(read)


@dataclass(frozen=True)
class ReadKey:
    """The key one stream of spectrums is read as, on both sides of the debouncer."""

    raw: tuple[bool, ...]
    debounced: tuple[bool, ...]


def read_key(spectrums: tuple[ToneSpectrum, ...]) -> ReadKey:
    """What the stages make of ``spectrums``, and what they would without a debouncer.

    The debounced side comes off the pipeline itself: the four stages meet there,
    and nowhere else is the key read the way the pipeline reads it.
    """
    return ReadKey(raw=keys(key_off(spectrums)), debounced=flags(detect(spectrums)))
