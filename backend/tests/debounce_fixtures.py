"""Builders for the keys and the grids the debounce tests drive.

The debouncer never sees a spectrum: it reads one key at one time, so a test
writes a run of flags on a grid of stamps. What the delays turn on is how long
a side is held, not how many readings hold it — timelines therefore stamp their
readings with whole multiples of a ``timedelta`` step, so the grid stays exact
no matter how fine it is, and a rounded microsecond cannot move an edge.
"""

import datetime
from itertools import pairwise
from typing import Self

from audio_fixtures import EPOCH
from key_fixtures import flags
from stream_fixtures import stream

from morse_decoder.config import KeyingDebouncerSettings
from morse_decoder.pipeline.dto import DigitalTone
from morse_decoder.pipeline.stages.keying_debouncer.interface import KeyingDebouncer
from morse_decoder.pipeline.stages.keying_debouncer.timed_keying_debouncer import (
    TimedKeyingDebouncer,
)

SETTINGS = KeyingDebouncerSettings()
RISE_SECONDS = SETTINGS.debounce_rise_seconds
FALL_SECONDS = SETTINGS.debounce_fall_seconds

STEP_S = RISE_SECONDS / 4
SETTLE_SECONDS = FALL_SECONDS * 2
BETWEEN_DELAYS_SECONDS = (RISE_SECONDS + FALL_SECONDS) / 2


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

    def build(self) -> tuple[DigitalTone, ...]:
        return tuple(
            DigitalTone(ts=EPOCH + index * self._step, on=is_on)
            for index, is_on in enumerate(self._flags)
        )


def blip(
    is_on: bool, seconds: float, step_seconds: float = STEP_S
) -> tuple[DigitalTone, ...]:
    """A run of one side of ``seconds``, on a line resting on the other side."""
    return (
        KeyTimeline(step_seconds)
        .hold(not is_on, SETTLE_SECONDS)
        .hold(is_on, seconds)
        .hold(not is_on, SETTLE_SECONDS)
        .build()
    )


def debouncer(settings: KeyingDebouncerSettings | None = None) -> TimedKeyingDebouncer:
    return TimedKeyingDebouncer(settings or SETTINGS)


async def debounce(
    readings: tuple[DigitalTone, ...],
    *,
    keying_debouncer: KeyingDebouncer | None = None,
) -> tuple[DigitalTone, ...]:
    """Feed ``readings`` to one debouncer the way the pipeline would."""
    reader = keying_debouncer or debouncer()
    return tuple([one async for one in reader.process(stream(*readings))])


async def debounced(
    readings: tuple[DigitalTone, ...],
    *,
    keying_debouncer: KeyingDebouncer | None = None,
) -> tuple[bool, ...]:
    """The key as one debouncer reads it off ``readings``."""
    return flags(await debounce(readings, keying_debouncer=keying_debouncer))


def edges(keys: tuple[bool, ...]) -> int:
    """How often the key changes side over ``keys``."""
    return sum(one != other for one, other in pairwise(keys))


async def keyed_seconds(readings: tuple[DigitalTone, ...]) -> float:
    """How long the debounced key stays down over ``readings`` of one grid."""
    step = (readings[1].ts - readings[0].ts).total_seconds()
    return sum(await debounced(readings)) * step
