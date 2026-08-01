from __future__ import annotations

from abc import ABC, abstractmethod

from morse_decoder.pipeline.dto import ToneSample
from morse_decoder.pipeline.stages.keying_debouncer.impl.policy import KeyingDelayPolicy


class DebouncedState(ABC):
    """FSM for debouncing keying signals."""

    @abstractmethod
    def update(self, sample: ToneSample) -> DebouncedState: ...

    @abstractmethod
    def is_on(self) -> bool: ...


class SettledState(DebouncedState):
    """The side the key has held long enough to be reported."""

    def __init__(self, policy: KeyingDelayPolicy, is_on: bool) -> None:
        self._policy = policy
        self._is_on = is_on

    def update(self, sample: ToneSample) -> DebouncedState:
        if sample.on == self._is_on:
            return self
        pending = PendingState(self._policy, settled=self._is_on, candidate=sample)
        return pending.update(sample)

    def is_on(self) -> bool:
        return self._is_on


class PendingState(DebouncedState):
    """A change begun but not yet held out; the settled side is what is reported."""

    def __init__(
        self, policy: KeyingDelayPolicy, settled: bool, candidate: ToneSample
    ) -> None:
        self._policy = policy
        self._settled = settled
        self._candidate = candidate

    def update(self, sample: ToneSample) -> DebouncedState:
        if sample.on == self._settled:
            return SettledState(self._policy, self._settled)
        if self._policy.is_held(self._candidate, sample.ts):
            return SettledState(self._policy, self._candidate.on)
        return self

    def is_on(self) -> bool:
        return self._settled
