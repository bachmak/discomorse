import datetime
from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import CarrierSourceSettings
from morse_decoder.pipeline.dto import CarrierSample, Tone, ToneSpectrum
from morse_decoder.pipeline.stages.carrier_source.impl.fsm import (
    CarrierTrackingState,
    SearchState,
)
from morse_decoder.pipeline.stages.carrier_source.impl.policy import CarrierLockPolicy
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource


class PeakCarrierSource(CarrierSource):
    """Reads the carrier off the loudest bin it is given, then holds it.

    Drives the tracking machine: each spectrum moves it into its next state.
    """

    def __init__(self, settings: CarrierSourceSettings) -> None:
        self._state: CarrierTrackingState = SearchState(
            policy=CarrierLockPolicy(
                min_magnitude=settings.carrier_lock_magnitude,
                tolerance_hz=settings.carrier_lock_tolerance_hz,
                lock_time=datetime.timedelta(seconds=settings.carrier_lock_seconds),
                hold_time=datetime.timedelta(seconds=settings.carrier_hold_seconds),
            ),
            candidate=Tone.empty(),
        )

    async def process(
        self, spectrums: AsyncIterable[ToneSpectrum]
    ) -> AsyncIterator[CarrierSample]:
        async for spectrum in spectrums:
            for carrier in self._advance(spectrum):
                yield carrier
        for carrier in self._state.flush():
            yield carrier

    def _advance(self, spectrum: ToneSpectrum) -> tuple[CarrierSample, ...]:
        peak = _loudest_tone_in_spectrum(spectrum)
        transition = self._state.update(peak, spectrum)
        self._state = transition.state
        return transition.reported_carriers


def _loudest_tone_in_spectrum(spectrum: ToneSpectrum) -> Tone:
    tone = max(spectrum.magnitudes, key=lambda tone: tone.magnitude)
    return Tone(
        frequency=tone.frequency,
        magnitude=tone.magnitude,
        ts=spectrum.ts,
    )
