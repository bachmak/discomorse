from morse_decoder.config import KeyingDetectorSettings
from morse_decoder.pipeline.dto import CarrierSample, KeyingSample, NoiseSample
from morse_decoder.pipeline.stages.keying_detector.dto import KeyingThresholds
from morse_decoder.pipeline.stages.keying_detector.impl.fsm import KeyingState, OffState
from morse_decoder.pipeline.stages.keying_detector.impl.threshold_tracker import (
    ThresholdTracker,
)
from morse_decoder.pipeline.stages.keying_detector.interface import KeyingDetector


class AdaptiveKeyingDetector(KeyingDetector):
    """Detect on and offs based on dynamically tracked thresholds."""

    def __init__(self, settings: KeyingDetectorSettings) -> None:
        self._thresholds = ThresholdTracker(settings)
        self._state: KeyingState = OffState()

    def detect(self, carrier: CarrierSample, noise: NoiseSample) -> KeyingSample:
        thresholds = self._thresholds.update(noise)
        self._state = self._next_state(carrier, thresholds)
        return self._state.get_keying()

    def _next_state(
        self, carrier: CarrierSample, thresholds: KeyingThresholds
    ) -> KeyingState:
        if not carrier.is_locked:
            return OffState()
        return self._state.update(carrier.tone.magnitude, thresholds)
