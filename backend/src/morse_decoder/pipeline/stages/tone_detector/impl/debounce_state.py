from __future__ import annotations

import datetime
from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.tone_detector.impl.debounce_policy import (
    KeyingDelayPolicy,
)
from morse_decoder.pipeline.stages.tone_detector.impl.dto import KeyingSample


class DebouncedKey(ABC):
    """One state of the debouncing machine.

    Every reading drives one transition: ``update`` names the state it moves the
    machine into, and that state reports the key the stage stands behind.
    """

    @abstractmethod
    def update(self, sample: KeyingSample, ts: datetime.datetime) -> DebouncedKey: ...

    @abstractmethod
    def get_keying(self) -> KeyingSample: ...


class SettledKey(DebouncedKey):
    """The side the key has held long enough to be reported."""

    def __init__(self, policy: KeyingDelayPolicy, keying: KeyingSample) -> None:
        self._policy = policy
        self._keying = keying

    def update(self, sample: KeyingSample, ts: datetime.datetime) -> DebouncedKey:
        if sample == self._keying:
            return self
        return self._begin(sample, ts)

    def _begin(self, candidate: KeyingSample, ts: datetime.datetime) -> DebouncedKey:
        """A change is weighed from the reading it is seen in, not from the next one."""
        pending = PendingKey(self._policy, self._keying, candidate, ts)
        return pending.update(candidate, ts)

    def get_keying(self) -> KeyingSample:
        return self._keying


class PendingKey(DebouncedKey):
    """A change begun but not yet held out; the settled side is what is reported."""

    def __init__(
        self,
        policy: KeyingDelayPolicy,
        settled: KeyingSample,
        candidate: KeyingSample,
        since: datetime.datetime,
    ) -> None:
        self._policy = policy
        self._settled = settled
        self._candidate = candidate
        self._since = since

    def update(self, sample: KeyingSample, ts: datetime.datetime) -> DebouncedKey:
        if sample == self._settled:
            return SettledKey(self._policy, self._settled)
        if self._policy.is_held(self._candidate, self._since, ts):
            return SettledKey(self._policy, self._candidate)
        return self

    def get_keying(self) -> KeyingSample:
        return self._settled
