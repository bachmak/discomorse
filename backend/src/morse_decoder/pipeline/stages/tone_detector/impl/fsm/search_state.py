from __future__ import annotations

from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    Tone,
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

    def __init__(self, policy: CarrierLockPolicy, candidate: Tone) -> None:
        self._policy = policy
        self._candidate = candidate

    def update(self, peak: Tone, _: ToneSpectrum) -> CarrierTrackingState:
        candidate = self._updated_candidate(peak)
        if self._policy.is_persistent(candidate, peak.ts):
            return HoldState(self._policy, carrier=peak, rival=Tone.empty())
        return SearchState(self._policy, candidate)

    def _updated_candidate(self, peak: Tone) -> Tone:
        if not self._policy.is_credible(peak.magnitude):
            return Tone.empty()
        if self._policy.continues(self._candidate, peak):
            return self._candidate
        return peak

    def get_carrier(self, peak: Tone) -> CarrierSample:
        return CarrierSample(
            tone=peak,
            is_locked=False,
        )
