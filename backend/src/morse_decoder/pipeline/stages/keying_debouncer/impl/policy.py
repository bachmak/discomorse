import datetime

from morse_decoder.pipeline.dto import ToneSample


class KeyingDelayPolicy:
    """How long each side of the key has to hold before the change is believed."""

    def __init__(self, rise: datetime.timedelta, fall: datetime.timedelta) -> None:
        self._rise = rise
        self._fall = fall

    def is_held(self, candidate: ToneSample, ts: datetime.datetime) -> bool:
        return ts - candidate.ts >= self._delay_of(candidate)

    def _delay_of(self, candidate: ToneSample) -> datetime.timedelta:
        return self._rise if candidate.on else self._fall
