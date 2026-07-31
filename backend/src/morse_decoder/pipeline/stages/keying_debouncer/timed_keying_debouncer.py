import datetime

from morse_decoder.config import KeyingDebouncerSettings
from morse_decoder.pipeline.dto import KeyingSample
from morse_decoder.pipeline.stages.keying_debouncer.impl.fsm import (
    DebouncedState,
    SettledState,
)
from morse_decoder.pipeline.stages.keying_debouncer.impl.policy import KeyingDelayPolicy
from morse_decoder.pipeline.stages.keying_debouncer.interface import KeyingDebouncer


class TimedKeyingDebouncer(KeyingDebouncer):
    """Passes a change on only once the key has kept its new side long enough.

    Drives the debouncing FSM: each reading moves it into its next state.
    """

    def __init__(self, settings: KeyingDebouncerSettings) -> None:
        self._state: DebouncedState = SettledState(
            policy=KeyingDelayPolicy(
                rise=datetime.timedelta(seconds=settings.debounce_rise_seconds),
                fall=datetime.timedelta(seconds=settings.debounce_fall_seconds),
            ),
            keying=KeyingSample(is_on=False),
        )

    def debounce(self, sample: KeyingSample, ts: datetime.datetime) -> KeyingSample:
        self._state = self._state.update(sample, ts)
        return self._state.get_keying()
