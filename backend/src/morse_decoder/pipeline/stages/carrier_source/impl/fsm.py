"""The state machine that tracks the carrier: it searches, then it locks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from morse_decoder.pipeline.dto import CarrierSample, Tone, ToneSpectrum
from morse_decoder.pipeline.stages.carrier_source.impl.policy import CarrierLockPolicy


@dataclass(frozen=True)
class StateTransition:
    state: CarrierTrackingState
    reported_carriers: tuple[CarrierSample, ...]


class CarrierTrackingState(ABC):
    """One state of the carrier tracking machine."""

    @abstractmethod
    def update(self, peak: Tone, spectrum: ToneSpectrum) -> StateTransition: ...

    @abstractmethod
    def flush(self) -> tuple[CarrierSample, ...]: ...


class SearchState(CarrierTrackingState):
    """Watches one frequency until it has repeated long enough to be the carrier."""

    def __init__(
        self,
        policy: CarrierLockPolicy,
        candidate: Tone,
        postponed_carriers: tuple[Tone, ...] = (),
    ) -> None:
        self._policy = policy
        self._candidate = candidate
        self._postponed_carriers = postponed_carriers

    def update(self, peak: Tone, _: ToneSpectrum) -> StateTransition:
        if not self._policy.is_credible(peak.magnitude):
            return self._to_new_empty_search_state(peak)
        if not self._policy.continues(self._candidate, peak):
            return self._to_new_populated_search_state(peak)
        return self._maybe_move_to_hold_state(peak)

    def flush(self) -> tuple[CarrierSample, ...]:
        return _assign_is_locked(self._postponed_carriers, False)

    def _to_new_empty_search_state(self, peak: Tone) -> StateTransition:
        reported_carriers = self._postponed_carriers + (peak,)
        return StateTransition(
            state=SearchState(self._policy, Tone.empty()),
            reported_carriers=_assign_is_locked(reported_carriers, False),
        )

    def _to_new_populated_search_state(self, peak: Tone) -> StateTransition:
        return StateTransition(
            state=SearchState(self._policy, peak, (peak,)),
            reported_carriers=_assign_is_locked(self._postponed_carriers, False),
        )

    def _maybe_move_to_hold_state(self, peak: Tone) -> StateTransition:
        if self._policy.is_persistent(self._candidate, peak.ts):
            reported_carriers = self._postponed_carriers + (peak,)
            return StateTransition(
                state=HoldState.create(self._policy, peak),
                reported_carriers=_assign_is_locked(reported_carriers, True),
            )

        postponed_carriers = self._postponed_carriers + (peak,)
        return StateTransition(
            state=SearchState(self._policy, self._candidate, postponed_carriers),
            reported_carriers=(),
        )


class HoldState(CarrierTrackingState):
    """Keeps the acquired frequency and reports how loud the band is around it."""

    def __init__(
        self,
        policy: CarrierLockPolicy,
        carrier: Tone,
        max_carrier_magnitude: float,
        rival: Tone,
    ) -> None:
        self._policy = policy
        self._carrier = carrier
        self._max_carrier_magnitude = max_carrier_magnitude
        self._rival = rival

    @classmethod
    def create(cls, policy: CarrierLockPolicy, carrier: Tone) -> HoldState:
        return HoldState(policy, carrier, carrier.magnitude, Tone.empty())

    def update(self, peak: Tone, spectrum: ToneSpectrum) -> StateTransition:
        new_state = self._evaluate_new_state(peak, spectrum)
        carrier = CarrierSample(
            tone=new_state._carrier.with_ts(peak.ts),
            is_locked=True,
        )
        return StateTransition(
            state=new_state,
            reported_carriers=(carrier,),
        )

    def flush(self) -> tuple[CarrierSample, ...]:
        return ()

    def _evaluate_new_state(self, peak: Tone, spectrum: ToneSpectrum) -> HoldState:
        if not self._policy.is_credible(peak.magnitude):
            return self._clone(self._updated_carrier(spectrum), Tone.empty())

        if self._policy.continues(self._carrier, peak):
            return self._clone(peak, Tone.empty())

        if not self._policy.beats(
            prev_tone=self._carrier.with_magnitude(self._max_carrier_magnitude),
            new_tone=peak,
        ):
            return self._clone(self._updated_carrier(spectrum), Tone.empty())

        rival = self._updated_rival(peak)
        if not self._policy.is_persistent(rival, peak.ts):
            return self._clone(self._updated_carrier(spectrum), rival)

        return HoldState(self._policy, peak, peak.magnitude, Tone.empty())

    def _clone(self, carrier: Tone, rival: Tone) -> HoldState:
        return HoldState(
            policy=self._policy,
            carrier=carrier,
            max_carrier_magnitude=max(carrier.magnitude, self._max_carrier_magnitude),
            rival=rival,
        )

    def _updated_carrier(self, spectrum: ToneSpectrum) -> Tone:
        new_carrier_magnitude = _magnitude_at_nearest_freq(
            spectrum, self._carrier.frequency
        )

        return self._carrier.with_magnitude(new_carrier_magnitude)

    def _updated_rival(self, peak: Tone) -> Tone:
        if self._policy.continues(prev_tone=self._rival, new_tone=peak):
            return peak.with_ts(self._rival.ts)
        return peak


def _assign_is_locked(
    tones: tuple[Tone, ...], is_locked: bool
) -> tuple[CarrierSample, ...]:
    return tuple(CarrierSample(tone=tone, is_locked=is_locked) for tone in tones)


def _magnitude_at_nearest_freq(spectrum: ToneSpectrum, frequency: float) -> float:
    nearest_tone = min(
        spectrum.magnitudes,
        key=lambda tone: abs(tone.frequency - frequency),
    )
    return nearest_tone.magnitude
