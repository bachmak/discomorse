from abc import ABC, abstractmethod

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneMagnitude, ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierReading,
    CarrierSample,
    FrequencyWindow,
    SpectrumPeak,
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

    Drives the tracking machine: each spectrum moves it into its next state,
    and that state reads the carrier out. The machine lives on between calls,
    so a pause in the keying — and the reading boundary that a chunk of audio
    ends at — leaves the carrier where it was instead of letting the loudest
    bin of the noise stand in for it.
    """

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)
        self._state: CarrierTrackingState = SearchState.create(
            CarrierLockPolicy.from_settings(settings)
        )

    def track(self, reading: SpectrumReading) -> CarrierReading:
        return CarrierReading(
            samples=tuple(self._update(spectrum) for spectrum in reading.spectrums)
        )

    def _update(self, spectrum: ToneSpectrum) -> CarrierSample:
        peak = SpectrumPeak(
            spectrum=spectrum,
            tone=_loudest_tone_in_spectrum(spectrum, self._window),
        )
        self._state = self._state.update(peak)
        return self._state.read(peak)


def _loudest_tone_in_spectrum(
    spectrum: ToneSpectrum, window: FrequencyWindow
) -> ToneMagnitude:
    tones_inside_window = tuple(
        tone
        for tone in spectrum.magnitudes
        if window.min_hz <= tone.frequency <= window.max_hz
    )

    if not tones_inside_window:
        raise ValueError(f"no spectrum bin in {window.min_hz}..{window.max_hz} Hz")

    return max(tones_inside_window, key=lambda tone: tone.magnitude)
