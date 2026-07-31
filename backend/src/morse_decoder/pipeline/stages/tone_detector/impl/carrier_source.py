import datetime
from abc import ABC, abstractmethod

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierReading,
    CarrierSample,
    FrequencyWindow,
    Tone,
)
from morse_decoder.pipeline.stages.tone_detector.impl.fsm.search_state import (
    SearchState,
)
from morse_decoder.pipeline.stages.tone_detector.impl.fsm.state import (
    CarrierTrackingState,
)
from morse_decoder.pipeline.stages.tone_detector.impl.lock_policy import (
    CarrierLockPolicy,
)


class CarrierSource(ABC):
    @abstractmethod
    def track(self, reading: SpectrumReading) -> CarrierReading:
        """Follow the carrier through the spectrums of one reading."""
        ...


class PeakCarrierSource(CarrierSource):
    """Reads the carrier off the loudest bin of the configured window, then holds it.

    Drives the tracking machine: each spectrum moves it into its next state.
    """

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)
        self._state: CarrierTrackingState = SearchState(
            policy=CarrierLockPolicy(
                min_magnitude=settings.carrier_lock_magnitude,
                tolerance_hz=settings.carrier_lock_tolerance_hz,
                lock_time=datetime.timedelta(seconds=settings.carrier_lock_seconds),
                hold_time=datetime.timedelta(seconds=settings.carrier_hold_seconds),
            ),
            candidate=Tone.empty(),
        )

    def track(self, reading: SpectrumReading) -> CarrierReading:
        return CarrierReading(
            samples=tuple(self._update(spectrum) for spectrum in reading.spectrums)
        )

    def _update(self, spectrum: ToneSpectrum) -> CarrierSample:
        peak = _loudest_tone_in_spectrum(spectrum, self._window)
        self._state = self._state.update(peak, spectrum)
        return self._state.get_carrier(peak)


def _loudest_tone_in_spectrum(spectrum: ToneSpectrum, window: FrequencyWindow) -> Tone:
    tones_inside_window = tuple(
        tone
        for tone in spectrum.magnitudes
        if window.min_hz <= tone.frequency <= window.max_hz
    )

    if not tones_inside_window:
        raise ValueError(f"no spectrum bin in {window.min_hz}..{window.max_hz} Hz")

    magnitude = max(tones_inside_window, key=lambda tone: tone.magnitude)
    return Tone(
        frequency=magnitude.frequency,
        magnitude=magnitude.magnitude,
        ts=spectrum.ts,
    )
