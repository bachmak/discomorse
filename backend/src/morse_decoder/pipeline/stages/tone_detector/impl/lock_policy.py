import datetime

from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    Tone,
)


def _is_valid(tone: Tone) -> bool:
    return (
        tone.ts != datetime.datetime.min
        and tone.frequency != 0.0
        and tone.magnitude != 0.0
    )


class CarrierLockPolicy:
    """How loud a peak must be, how far it may move, and how often it must repeat."""

    def __init__(
        self,
        min_magnitude: float,
        tolerance_hz: float,
        lock_time: datetime.timedelta,
        hold_time: datetime.timedelta,
    ) -> None:
        self._min_magnitude = min_magnitude
        self._tolerance_hz = tolerance_hz
        self._lock_time = lock_time
        self._hold_time = hold_time

    def is_credible(self, magnitude: float) -> bool:
        """Whether a level stands out enough to be a carrier rather than noise."""
        return magnitude >= self._min_magnitude

    def continues(self, prev_tone: Tone, new_tone: Tone) -> bool:
        if not _is_valid(new_tone):
            return False

        return abs(prev_tone.frequency - new_tone.frequency) <= self._tolerance_hz

    def is_persistent(self, tone: Tone, ts: datetime.datetime) -> bool:
        return _is_valid(tone) and (ts >= tone.ts + self._lock_time)

    def beats(self, prev_tone: Tone, new_tone: Tone) -> bool:
        if not self.is_credible(new_tone.magnitude):
            return False
        if new_tone.ts > prev_tone.ts + self._hold_time:
            return True
        return new_tone.magnitude >= prev_tone.magnitude
