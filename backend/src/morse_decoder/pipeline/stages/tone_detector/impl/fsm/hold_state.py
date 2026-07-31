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
        rival: Tone,
    ) -> None:
        self._policy = policy
        self._carrier = carrier
        self._rival = rival

    def update(self, peak: Tone, spectrum: ToneSpectrum) -> CarrierTrackingState:
        if not self._policy.is_credible(peak.magnitude):
            return self._clone(self._carrier, Tone.empty())

        if self._policy.continues(self._carrier, peak):
            new_carrier = Tone(
                frequency=peak.frequency,
                magnitude=max(self._carrier.magnitude, peak.magnitude),
                ts=peak.ts,
            )
            return self._clone(new_carrier, Tone.empty())

        carrier = self._updated_carrier(spectrum)
        if not self._policy.beats(prev_tone=carrier, new_tone=peak):
            return self._clone(carrier, Tone.empty())

        rival = self._updated_rival(peak)
        if not self._policy.is_persistent(rival, peak.ts):
            return self._clone(carrier, rival)

        return self._clone(peak, Tone.empty())

    def get_carrier(self, peak: Tone) -> CarrierSample:
        return CarrierSample(
            tone=self._carrier,
            is_locked=True,
        )

    def _clone(self, carrier: Tone, rival: Tone) -> HoldState:
        return HoldState(self._policy, carrier, rival)

    def _updated_carrier(self, spectrum: ToneSpectrum) -> Tone:
        new_carrier_magnitude = _magnitude_at_nearest_freq(
            spectrum, self._carrier.frequency
        )

        if not self._policy.is_credible(new_carrier_magnitude):
            return self._carrier

        return Tone(
            frequency=self._carrier.frequency,
            magnitude=new_carrier_magnitude,
            ts=spectrum.ts,
        )

    def _updated_rival(self, peak: Tone) -> Tone:
        if self._policy.continues(prev_tone=self._rival, new_tone=peak):
            return Tone(
                frequency=peak.frequency,
                magnitude=peak.magnitude,
                ts=self._rival.ts,
            )
        return peak


def _magnitude_at_nearest_freq(spectrum: ToneSpectrum, frequency: float) -> float:
    nearest_tone = min(
        spectrum.magnitudes,
        key=lambda tone: abs(tone.frequency - frequency),
    )
    return nearest_tone.magnitude
