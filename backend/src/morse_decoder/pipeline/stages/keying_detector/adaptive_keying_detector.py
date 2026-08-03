from morse_decoder.config import KeyingDetectorSettings
from morse_decoder.pipeline.dto import CarrierNoiseSample, CarrierSample, ToneSample
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

    def process_single(self, sample: CarrierNoiseSample) -> ToneSample:
        thresholds = self._thresholds.update(sample.noise)
        self._state = self._next_state(sample.carrier, thresholds)
        return ToneSample(ts=sample.carrier.tone.ts, on=self._state.is_on())

    def _next_state(
        self, carrier: CarrierSample, thresholds: KeyingThresholds
    ) -> KeyingState:
        if not carrier.is_locked:
            return OffState()
        return self._state.update(carrier.tone.magnitude, thresholds)
