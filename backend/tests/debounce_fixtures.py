"""Builders for the keys and the grids the debounce tests drive.

The debouncer never sees a spectrum: it reads one key at one time, so a test
writes a run of flags on a grid of stamps. What the delays turn on is how long
a side is held, not how many readings hold it — timelines therefore stamp their
readings with whole multiples of a ``timedelta`` step, so the grid stays exact
no matter how fine it is, and a rounded microsecond cannot move an edge.
"""

import datetime
from dataclasses import dataclass
from itertools import pairwise
from typing import Self

from audio_fixtures import EPOCH
from carrier_fixtures import SETTINGS
from keying_fixtures import key_off, keys
from tone_fixtures import detect, flags

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import KeyingSample
from morse_decoder.pipeline.stages.tone_detector.impl.keying_debouncer import (
    TimedKeyingDebouncer,
)

RISE_SECONDS = SETTINGS.debounce_rise_seconds
FALL_SECONDS = SETTINGS.debounce_fall_seconds

STEP_S = RISE_SECONDS / 4
SETTLE_SECONDS = FALL_SECONDS * 2
BETWEEN_DELAYS_SECONDS = (RISE_SECONDS + FALL_SECONDS) / 2


@dataclass(frozen=True)
class KeyReading:
    """One reading as the debouncer sees it: a key and the time it was read."""

    sample: KeyingSample
    ts: datetime.datetime


class KeyTimeline:
    """Keys on a fixed grid: one reading every ``step_seconds``."""

    def __init__(self, step_seconds: float = STEP_S) -> None:
        self._step = datetime.timedelta(seconds=step_seconds)
        self._flags: list[bool] = []

    def add(self, is_on: bool, count: int = 1) -> Self:
        self._flags += [is_on] * count
        return self

    def hold(self, is_on: bool, seconds: float) -> Self:
        """Stay on one side for as many whole steps as fit in ``seconds``."""
        return self.add(is_on, self.steps_in(seconds))

    def alternate(self, cycles: int, run: int = 1) -> Self:
        """Swap sides, ``run`` readings of each, ``cycles`` times over."""
        for _ in range(cycles):
            self.add(True, run).add(False, run)
        return self

    def steps_in(self, seconds: float) -> int:
        return round(datetime.timedelta(seconds=seconds) / self._step)

    def build(self) -> tuple[KeyReading, ...]:
        return tuple(
            KeyReading(KeyingSample(is_on=is_on), EPOCH + index * self._step)
            for index, is_on in enumerate(self._flags)
        )


def blip(
    is_on: bool, seconds: float, step_seconds: float = STEP_S
) -> tuple[KeyReading, ...]:
    """A run of one side of ``seconds``, on a line resting on the other side."""
    return (
        KeyTimeline(step_seconds)
        .hold(not is_on, SETTLE_SECONDS)
        .hold(is_on, seconds)
        .hold(not is_on, SETTLE_SECONDS)
        .build()
    )


def debouncer(settings: ToneDetectorSettings | None = None) -> TimedKeyingDebouncer:
    return TimedKeyingDebouncer(settings or SETTINGS)


def debounce(
    readings: tuple[KeyReading, ...],
    *,
    keying_debouncer: TimedKeyingDebouncer | None = None,
) -> tuple[KeyingSample, ...]:
    """Feed ``readings`` to one debouncer the way the tone detector would."""
    reader = keying_debouncer or debouncer()
    return tuple(reader.debounce(one.sample, one.ts) for one in readings)


def debounced(
    readings: tuple[KeyReading, ...],
    *,
    keying_debouncer: TimedKeyingDebouncer | None = None,
) -> tuple[bool, ...]:
    """The key as one debouncer reads it off ``readings``."""
    return tuple(
        sample.is_on for sample in debounce(readings, keying_debouncer=keying_debouncer)
    )


def edges(flags: tuple[bool, ...]) -> int:
    """How often the key changes side over ``flags``."""
    return sum(one != other for one, other in pairwise(flags))


def keyed_seconds(readings: tuple[KeyReading, ...]) -> float:
    """How long the debounced key stays down over ``readings`` of one grid."""
    step = (readings[1].ts - readings[0].ts).total_seconds()
    return sum(debounced(readings)) * step


@dataclass(frozen=True)
class ReadKey:
    """The key one stream of spectrums is read as, on both sides of the debouncer."""

    raw: tuple[bool, ...]
    debounced: tuple[bool, ...]


async def read_key(spectrums: tuple[ToneSpectrum, ...]) -> ReadKey:
    """What the stage makes of ``spectrums``, and what it would without a debouncer.

    The debounced side comes off the stage itself: the four substages meet there,
    and nowhere else is the key read the way the pipeline reads it.
    """
    return ReadKey(
        raw=keys(key_off(spectrums)),
        debounced=flags(await detect(spectrums)),
    )
