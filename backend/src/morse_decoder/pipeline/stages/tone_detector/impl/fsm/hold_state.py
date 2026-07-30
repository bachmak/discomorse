from __future__ import annotations

from morse_decoder.pipeline.dto import ToneMagnitude, ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierCandidate,
    CarrierSample,
    SpectrumPeak,
)
from morse_decoder.pipeline.stages.tone_detector.impl.fsm.state import (
    CarrierTrackingState,
)
from morse_decoder.pipeline.stages.tone_detector.impl.lock_policy import (
    CarrierLockPolicy,
)


class HoldState(CarrierTrackingState):
    """Keeps the acquired frequency and reports how loud the band is around it.

    A pause leaves the frequency untouched instead of handing it to whatever
    noise happens to be loudest, so the carrier outlives both silence and the
    boundary between two readings. Drift inside the tolerance is followed as it
    happens; only a rival that keeps coming back takes the lock over. Either
    way the machine stays here — it never searches again.
    """

    def __init__(
        self,
        policy: CarrierLockPolicy,
        frequency: float,
        rival: CarrierCandidate,
    ) -> None:
        self._policy = policy
        self._frequency = frequency
        self._rival = rival

    @classmethod
    def create(cls, policy: CarrierLockPolicy, frequency: float) -> HoldState:
        return cls(policy, frequency, CarrierCandidate.empty())

    def update(self, peak: SpectrumPeak) -> CarrierTrackingState:
        if self._policy.follows(self._frequency, peak.tone):
            return HoldState.create(self._policy, peak.tone.frequency)
        return self._challenged_by(peak.tone)

    def read(self, peak: SpectrumPeak) -> CarrierSample:
        return CarrierSample(
            ts=peak.spectrum.ts,
            frequency=self._frequency,
            magnitude=_magnitude_at_nearest_freq(peak.spectrum, self._frequency),
            is_locked=True,
        )

    def _challenged_by(self, peak: ToneMagnitude) -> HoldState:
        rival = self._policy.sighted(self._rival, peak)
        if self._policy.confirms(rival):
            return HoldState.create(self._policy, rival.frequency)
        return HoldState(self._policy, self._frequency, rival)


def _magnitude_at_nearest_freq(spectrum: ToneSpectrum, frequency: float) -> float:
    nearest_tone = min(
        spectrum.magnitudes,
        key=lambda tone: abs(tone.frequency - frequency),
    )
    return nearest_tone.magnitude
