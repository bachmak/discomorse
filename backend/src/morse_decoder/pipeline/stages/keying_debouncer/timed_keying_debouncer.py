import datetime
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import KeyingDebouncerSettings
from morse_decoder.pipeline.dto import DigitalTone
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
            is_on=False,
        )

    async def process(
        self, samples: AsyncIterable[DigitalTone]
    ) -> AsyncIterator[DigitalTone]:
        async for sample in samples:
            transition = self._state.update(sample)
            self._state = transition.state
            for published_sample in transition.reported_samples:
                yield published_sample
