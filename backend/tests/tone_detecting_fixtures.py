"""Tone detecting: the four stages that turn spectrums into a keyed line.

Carrier source, noise estimator, keying detector and debouncer only meet in the
pipeline, so a test that wants them together drives the ones a real pipeline
built, chained here the way ``Pipeline.run`` chains them.
"""

from collections.abc import AsyncIterable, AsyncIterator, Iterable
from dataclasses import dataclass

import numpy.typing as npt
from carrier_fixtures import ANALYZER_SETTINGS
from key_fixtures import flags
from keying_fixtures import key_off, readings_off
from limiter_fixtures import limit
from spectrum_fixtures import spectrums_of
from stream_fixtures import stream
from tone_fixtures import PcmChunks

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

    async def read(self, spectrums: tuple[ToneSpectrum, ...]) -> tuple[ToneSample, ...]:
        limited = await limit(
            spectrums, spectrum_limiter=self._pipeline._spectrum_limiter
        )
        return tuple([sample async for sample in self._samples(stream(*limited))])

    def _samples(
        self, limited: AsyncIterable[ToneSpectrum]
    ) -> AsyncIterator[ToneSample]:
        """The key the four stages read, one sample per spectrum they are given."""
        readings = readings_off(
            limited, self._pipeline._carrier_source, self._pipeline._noise_estimator
        )
        return self._pipeline._keying_debouncer.process(
            self._pipeline._keying_detector.process(readings)
        )

    async def read_chunks(self, chunks: Iterable[PcmChunk]) -> tuple[ToneSample, ...]:
        """Every chunk as the one stream ``run`` reads, however many they are."""
        limited = self._pipeline._spectrum_limiter.process(
            self._pipeline._spectrum_analyzer.process(stream(*chunks))
        )
        return tuple([sample async for sample in self._samples(limited)])

    async def feed(self, chunk: PcmChunk) -> tuple[ToneSample, ...]:
        """One chunk of audio, read as a stream that ends with it."""
        spectrums = await spectrums_of(self._pipeline._spectrum_analyzer, chunk)
        return await self.read(spectrums)

    def stage[StageT](self, name: str, kind: type[StageT]) -> StageT:
        """The stage the pipeline built under ``name``, told to be a ``kind``."""
        stage = getattr(self._pipeline, f"_{name}")
        assert isinstance(stage, kind)
        return stage


def tone_detecting(settings: PipelineSettings | None = None) -> ToneDetecting:
    return ToneDetecting(create_pipeline(NoAudio(), settings or SETTINGS))


async def detect(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    detecting: ToneDetecting | None = None,
) -> tuple[ToneSample, ...]:
    """Feed ``spectrums`` to one set of stages the way the pipeline would."""
    return await (detecting or tone_detecting()).read(spectrums)


async def read_tone(
    samples: npt.NDArray[PCM16.IntType], chunks: int = 1
) -> tuple[ToneSample, ...]:
    """The key one set of stages reads off ``samples`` handed to it in ``chunks``."""
    return await tone_detecting().read_chunks(PcmChunks(samples, chunks))


@dataclass(frozen=True)
class ReadKey:
    """The key one stream of spectrums is read as, on both sides of the debouncer."""

    raw: tuple[bool, ...]
    debounced: tuple[bool, ...]


async def read_key(spectrums: tuple[ToneSpectrum, ...]) -> ReadKey:
    """What the stages make of ``spectrums``, and what they would without a debouncer.

    The debounced side comes off the pipeline itself: the four stages meet there,
    and nowhere else is the key read the way the pipeline reads it.
    """
    return ReadKey(
        raw=flags(await key_off(spectrums)), debounced=flags(await detect(spectrums))
    )
