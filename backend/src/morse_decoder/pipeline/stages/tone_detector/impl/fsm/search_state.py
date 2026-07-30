from __future__ import annotations

from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierCandidate,
    CarrierSample,
    SpectrumPeak,
)
from morse_decoder.pipeline.stages.tone_detector.impl.fsm.hold_state import HoldState
from morse_decoder.pipeline.stages.tone_detector.impl.fsm.state import (
    CarrierTrackingState,
)
from morse_decoder.pipeline.stages.tone_detector.impl.lock_policy import (
    CarrierLockPolicy,
)


class SearchState(CarrierTrackingState):
    """Passes the loudest bin on unchanged until one frequency repeats enough."""

    def __init__(self, policy: CarrierLockPolicy, candidate: CarrierCandidate) -> None:
        self._policy = policy
        self._candidate = candidate

    @classmethod
    def create(cls, policy: CarrierLockPolicy) -> SearchState:
        return cls(policy, CarrierCandidate.empty())

    def update(self, peak: SpectrumPeak) -> CarrierTrackingState:
        candidate = self._policy.sighted(self._candidate, peak.tone)
        if self._policy.confirms(candidate):
            return HoldState.create(self._policy, candidate.frequency)
        return SearchState(self._policy, candidate)

    def read(self, peak: SpectrumPeak) -> CarrierSample:
        return CarrierSample(
            ts=peak.spectrum.ts,
            frequency=peak.tone.frequency,
            magnitude=peak.tone.magnitude,
            is_locked=False,
        )
