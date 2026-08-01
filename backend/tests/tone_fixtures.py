"""Builders for the audio the keying stages are driven with, and the key they read.

A test writes a line of marks and gaps in dit units and reads the answer back as
runs of the same shape, because runs of a keyed line are what the timing stage
lives on. How the line is fed through the stages is ``tone_detecting_fixtures``.

An edge cannot land where it was keyed: the frame it falls in reads both sides
of it at once, and the debouncer holds the new side back until it is believed.
``EDGE_DRIFT_SECONDS`` is how far that moves an edge, and what the tests here
allow a mark or a gap to differ from the length it was keyed with.
"""

import datetime
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import groupby
from typing import Self

import numpy as np
import numpy.typing as npt
from audio_fixtures import EPOCH, noise_pcm, silence_pcm, sine_pcm
from carrier_fixtures import FRAME_SECONDS, HOP_SECONDS, SAMPLE_RATE, Phase
from debounce_fixtures import FALL_SECONDS

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.dto import PcmChunk, ToneSample

TONE_HZ = 750.0
KEY_DOWN_AMPLITUDE = 0.5
DIT_SECONDS = 1.2 / 20  # a dit at the speed the timing stage is seeded with
EDGE_DRIFT_SECONDS = FRAME_SECONDS + FALL_SECONDS


@dataclass(frozen=True)
class Segment(ABC):
    """One stretch of the keyed line: which side the key is on, and for how long."""

    seconds: float

    @property
    @abstractmethod
    def is_on(self) -> bool:
        """The side of the key this stretch was keyed with."""
        ...

    @property
    @abstractmethod
    def label(self) -> str:
        """What this stretch is called when a test names it."""
        ...

    @abstractmethod
    def render(self) -> npt.NDArray[PCM16.IntType]:
        """This stretch as PCM."""
        ...


class Mark(Segment):
    """Key down: the tone sounds."""

    @property
    def is_on(self) -> bool:
        return True

    @property
    def label(self) -> str:
        return "mark"

    def render(self) -> npt.NDArray[PCM16.IntType]:
        return sine_pcm(TONE_HZ, self.seconds, SAMPLE_RATE, KEY_DOWN_AMPLITUDE)


class Gap(Segment):
    """Key up: nothing sounds."""

    @property
    def is_on(self) -> bool:
        return False

    @property
    def label(self) -> str:
        return "gap"

    def render(self) -> npt.NDArray[PCM16.IntType]:
        return silence_pcm(self.seconds, SAMPLE_RATE)


@dataclass(frozen=True)
class KeyedPhase(Phase):
    """A stretch of the line, and the side the key is meant to be on over it."""

    is_on: bool
    label: str

    def settled(self) -> "KeyedPhase":
        """What is left of the stretch once the edge into it has had time to land."""
        return KeyedPhase(
            self.start_s + EDGE_DRIFT_SECONDS, self.end_s, self.is_on, self.label
        )


class KeyedLine:
    """A line of marks and gaps, written in dit units and rendered as audio."""

    def __init__(self, dit_seconds: float = DIT_SECONDS) -> None:
        self._dit_seconds = dit_seconds
        self._segments: list[Segment] = []

    def mark(self, units: float = 1) -> Self:
        return self._add(Mark(units * self._dit_seconds))

    def gap(self, units: float = 1) -> Self:
        return self._add(Gap(units * self._dit_seconds))

    def pcm(self, noise_amplitude: float = 0.0) -> npt.NDArray[PCM16.IntType]:
        keyed = np.concatenate([segment.render() for segment in self._segments])
        if not noise_amplitude:
            return keyed
        floor = noise_pcm(len(keyed) / SAMPLE_RATE, SAMPLE_RATE, noise_amplitude)
        return np.asarray(keyed + floor, dtype=PCM16.IntType)

    def phases(self) -> tuple[KeyedPhase, ...]:
        """Where each stretch of the line begins and ends, in seconds."""
        phases: list[KeyedPhase] = []
        start = 0.0
        for segment in self._segments:
            phases.append(
                KeyedPhase(start, start + segment.seconds, segment.is_on, segment.label)
            )
            start += segment.seconds
        return tuple(phases)

    def marks(self) -> tuple[Segment, ...]:
        return tuple(segment for segment in self._segments if segment.is_on)

    def _add(self, segment: Segment) -> Self:
        self._segments.append(segment)
        return self


@dataclass(frozen=True)
class Run:
    """A stretch the stages read as one side of the key, and how long it lasted."""

    is_on: bool
    seconds: float


class PcmChunks:
    """One block of PCM cut into chunks, each stamped where its first sample sits."""

    def __init__(self, samples: npt.NDArray[PCM16.IntType], count: int = 1) -> None:
        self._samples = samples
        self._count = count

    def __iter__(self) -> Iterator[PcmChunk]:
        offset = 0
        for part in np.array_split(self._samples, self._count):
            yield PcmChunk(ts=EPOCH + _elapsed(offset), data=part.tobytes())
            offset += len(part)


def morse_line() -> KeyedLine:
    """'AN T': every element length a straight key produces, spaced as morse."""
    return KeyedLine().mark().gap().mark(3).gap(3).mark(3).gap().mark().gap(7).mark(3)


def runs(samples: tuple[ToneSample, ...]) -> tuple[Run, ...]:
    """The samples gathered into the stretches the key held one side over."""
    return tuple(
        Run(is_on=is_on, seconds=len(tuple(group)) * HOP_SECONDS)
        for is_on, group in groupby(samples, key=lambda sample: sample.on)
    )


def keyed_runs(samples: tuple[ToneSample, ...]) -> tuple[Run, ...]:
    return tuple(run for run in runs(samples) if run.is_on)


def inside(
    samples: tuple[ToneSample, ...], phase: KeyedPhase
) -> tuple[ToneSample, ...]:
    """The samples of the frames that lie wholly inside ``phase``."""
    return tuple(sample for sample in samples if phase.covers(sample.ts))


def _elapsed(samples: int) -> datetime.timedelta:
    return datetime.timedelta(seconds=samples / SAMPLE_RATE)
