import datetime

from morse_decoder.pipeline.stages.tone_detector.impl.dto import KeyingSample


class KeyingDelayPolicy:
    """How long each side of the key has to hold before the change is believed."""

    def __init__(self, rise: datetime.timedelta, fall: datetime.timedelta) -> None:
        self._rise = rise
        self._fall = fall

    def is_held(
        self,
        candidate: KeyingSample,
        since: datetime.datetime,
        ts: datetime.datetime,
    ) -> bool:
        return ts - since >= self._delay_of(candidate)

    def _delay_of(self, candidate: KeyingSample) -> datetime.timedelta:
        return self._rise if candidate.is_on else self._fall
