from abc import ABC, abstractmethod

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    KeyingSample,
    KeyingThresholds,
    NoiseSample,
)
from morse_decoder.pipeline.stages.tone_detector.impl.keying_state import (
    KeyingState,
    OffState,
)
from morse_decoder.pipeline.stages.tone_detector.impl.threshold_tracker import (
    ThresholdTracker,
)


class KeyingDetector(ABC):
    @abstractmethod
    def detect(self, carrier: CarrierSample, noise: NoiseSample) -> KeyingSample: ...


class AdaptiveKeyingDetector(KeyingDetector):
    """Detect on and offs based on dynamically tracked thresholds."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
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
