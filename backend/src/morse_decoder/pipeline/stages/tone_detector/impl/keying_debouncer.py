import datetime
from abc import ABC, abstractmethod

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.stages.tone_detector.impl.debounce_policy import (
    KeyingDelayPolicy,
)
from morse_decoder.pipeline.stages.tone_detector.impl.debounce_state import (
    DebouncedKey,
    SettledKey,
)
from morse_decoder.pipeline.stages.tone_detector.impl.dto import KeyingSample


class KeyingDebouncer(ABC):
    @abstractmethod
    def debounce(self, sample: KeyingSample, ts: datetime.datetime) -> KeyingSample: ...


class TimedKeyingDebouncer(KeyingDebouncer):
    """Passes a change on only once the key has kept its new side long enough.

    Drives the debouncing machine: each reading moves it into its next state.
    """

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._key: DebouncedKey = SettledKey(
            policy=KeyingDelayPolicy(
                rise=datetime.timedelta(seconds=settings.debounce_rise_seconds),
                fall=datetime.timedelta(seconds=settings.debounce_fall_seconds),
            ),
            keying=KeyingSample(is_on=False),
        )

    def debounce(self, sample: KeyingSample, ts: datetime.datetime) -> KeyingSample:
        self._key = self._key.update(sample, ts)
        return self._key.get_keying()
