from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.pipeline.dto import DigitalTone
from morse_decoder.pipeline.stages.keying_debouncer.impl.policy import KeyingDelayPolicy


@dataclass(frozen=True)
class StateTransition:
    state: DebouncedState
    reported_samples: tuple[DigitalTone, ...]


class DebouncedState(ABC):
    """FSM for debouncing keying signals."""

    @abstractmethod
    def update(self, sample: DigitalTone) -> StateTransition: ...


class SettledState(DebouncedState):
    def __init__(self, policy: KeyingDelayPolicy, is_on: bool) -> None:
        self._policy = policy
        self._is_on = is_on

    def update(self, sample: DigitalTone) -> StateTransition:
        if sample.on == self._is_on:
            return StateTransition(state=self, reported_samples=(sample,))

        if self._policy.is_held(sample, sample.ts):
            return StateTransition(
                state=SettledState(self._policy, sample.on),
                reported_samples=(sample,),
            )

        return StateTransition(
            state=PendingState(self._policy, self._is_on, (sample,)),
            reported_samples=(),
        )


class PendingState(DebouncedState):
    def __init__(
        self,
        policy: KeyingDelayPolicy,
        settled_is_on: bool,
        postponed_samples: tuple[DigitalTone, ...],
    ) -> None:
        self._policy = policy
        self._settled_is_on = settled_is_on
        self._postponed_samples = postponed_samples
        self._first_stray_sample = postponed_samples[0]

    def update(self, sample: DigitalTone) -> StateTransition:
        if sample.on == self._settled_is_on:
            return self._to_old_settled(sample)

        if self._policy.is_held(self._first_stray_sample, sample.ts):
            return self._to_new_settled(sample)

        return self._stay_in_pending(sample)

    def _to_old_settled(self, sample: DigitalTone) -> StateTransition:
        reported_samples = self._postponed_samples + (sample,)
        return StateTransition(
            state=SettledState(self._policy, self._settled_is_on),
            reported_samples=_rewrite_is_on(reported_samples, self._settled_is_on),
        )

    def _to_new_settled(self, sample: DigitalTone) -> StateTransition:
        reported_samples = self._postponed_samples + (sample,)
        return StateTransition(
            state=SettledState(self._policy, sample.on),
            reported_samples=_rewrite_is_on(reported_samples, sample.on),
        )

    def _stay_in_pending(self, sample: DigitalTone) -> StateTransition:
        return StateTransition(
            state=PendingState(
                self._policy,
                self._settled_is_on,
                self._postponed_samples + (sample,),
            ),
            reported_samples=(),
        )


def _rewrite_is_on(
    samples: tuple[DigitalTone, ...], is_on: bool
) -> tuple[DigitalTone, ...]:
    return tuple(DigitalTone(ts=sample.ts, on=is_on) for sample in samples)
