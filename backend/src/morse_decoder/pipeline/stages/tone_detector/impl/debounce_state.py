from __future__ import annotations

import datetime
from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.tone_detector.impl.debounce_policy import (
    KeyingDelayPolicy,
)
from morse_decoder.pipeline.stages.tone_detector.impl.dto import KeyingSample


class DebouncedState(ABC):
    """FSM for debouncing keying signals."""

    @abstractmethod
    def update(self, sample: KeyingSample, ts: datetime.datetime) -> DebouncedState: ...

    @abstractmethod
    def get_keying(self) -> KeyingSample: ...


class SettledState(DebouncedState):
    """The side the key has held long enough to be reported."""

    def __init__(self, policy: KeyingDelayPolicy, keying: KeyingSample) -> None:
        self._policy = policy
        self._keying = keying

    def update(self, sample: KeyingSample, ts: datetime.datetime) -> DebouncedState:
        if sample == self._keying:
            return self
        pending = PendingState(
            self._policy,
            settled=self._keying,
            candidate=sample,
            since=ts,
        )
        return pending.update(sample, ts)

    def get_keying(self) -> KeyingSample:
        return self._keying


class PendingState(DebouncedState):
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

    def update(self, sample: KeyingSample, ts: datetime.datetime) -> DebouncedState:
        if sample == self._settled:
            return SettledState(self._policy, self._settled)
        if self._policy.is_held(self._candidate, self._since, ts):
            return SettledState(self._policy, self._candidate)
        return self

    def get_keying(self) -> KeyingSample:
        return self._settled
