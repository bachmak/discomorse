from typing import Self

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import ToneMagnitude
from morse_decoder.pipeline.stages.tone_detector.impl.dto import CarrierCandidate


class CarrierLockPolicy:
    """How loud a peak must be, how far it may move, and how often it must repeat.

    The tracking states ask the policy what a peak is worth; they never weigh
    magnitudes or frequency distances themselves.
    """

    def __init__(
        self, min_magnitude: float, tolerance_hz: float, min_confirmations: int
    ) -> None:
        self._min_magnitude = min_magnitude
        self._tolerance_hz = tolerance_hz
        self._min_confirmations = min_confirmations

    @classmethod
    def from_settings(cls, settings: ToneDetectorSettings) -> Self:
        return cls(
            min_magnitude=settings.carrier_lock_magnitude,
            tolerance_hz=settings.carrier_lock_tolerance_hz,
            min_confirmations=settings.carrier_lock_confirmations,
        )

    def sighted(
        self, candidate: CarrierCandidate, peak: ToneMagnitude
    ) -> CarrierCandidate:
        """The candidate this peak leaves behind: a run continued, restarted or lost."""
        if not self._is_credible(peak):
            return CarrierCandidate.empty()
        if self._continues(candidate, peak):
            return CarrierCandidate(peak.frequency, candidate.sightings + 1)
        return CarrierCandidate(peak.frequency, sightings=1)

    def confirms(self, candidate: CarrierCandidate) -> bool:
        """Whether the candidate has repeated often enough to be locked onto."""
        return candidate.sightings >= self._min_confirmations

    def follows(self, frequency: float, peak: ToneMagnitude) -> bool:
        """Whether a carrier held at ``frequency`` may drift onto this peak."""
        return self._is_credible(peak) and self._agrees(frequency, peak)

    def _continues(self, candidate: CarrierCandidate, peak: ToneMagnitude) -> bool:
        return (candidate.sightings > 0) and self._agrees(candidate.frequency, peak)

    def _is_credible(self, peak: ToneMagnitude) -> bool:
        return peak.magnitude >= self._min_magnitude

    def _agrees(self, frequency: float, peak: ToneMagnitude) -> bool:
        return abs(peak.frequency - frequency) <= self._tolerance_hz
