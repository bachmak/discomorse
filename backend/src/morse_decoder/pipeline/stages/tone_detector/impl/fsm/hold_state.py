from __future__ import annotations

from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    Tone,
)
from morse_decoder.pipeline.stages.tone_detector.impl.fsm.state import (
    CarrierTrackingState,
)
from morse_decoder.pipeline.stages.tone_detector.impl.lock_policy import (
    CarrierLockPolicy,
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

    def update(self, peak: Tone, spectrum: ToneSpectrum) -> CarrierTrackingState:
        carrier = self._updated_carrier(spectrum)
        if not self._policy.is_credible(peak.magnitude):
            return self._clone(carrier, Tone.empty())

        if self._policy.continues(self._carrier, peak):
            return self._clone(peak, Tone.empty())

        if not self._policy.beats(
            prev_tone=self._carrier.with_magnitude(self._max_carrier_magnitude),
            new_tone=peak,
        ):
            return self._clone(carrier, Tone.empty())

        rival = self._updated_rival(peak)
        if not self._policy.is_persistent(rival, peak.ts):
            return self._clone(carrier, rival)

        return HoldState(self._policy, peak, peak.magnitude, Tone.empty())

    def get_carrier(self, peak: Tone) -> CarrierSample:
        return CarrierSample(
            tone=self._carrier.with_ts(peak.ts),
            is_locked=True,
        )

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


def _magnitude_at_nearest_freq(spectrum: ToneSpectrum, frequency: float) -> float:
    nearest_tone = min(
        spectrum.magnitudes,
        key=lambda tone: abs(tone.frequency - frequency),
    )
    return nearest_tone.magnitude
