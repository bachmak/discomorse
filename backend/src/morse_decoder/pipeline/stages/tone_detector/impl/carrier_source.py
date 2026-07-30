from abc import ABC, abstractmethod

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.carrier import (
    CarrierReading,
    CarrierSample,
)
from morse_decoder.pipeline.stages.tone_detector.impl.frequency_window import (
    FrequencyWindow,
)


class CarrierSource(ABC):
    @abstractmethod
    def track(self, reading: SpectrumReading) -> CarrierReading:
        """Follow the carrier through the spectrums of one reading."""
        ...


class PeakCarrierSource(CarrierSource):
    """Reads the carrier off the loudest bin of the configured window."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._window = FrequencyWindow(settings.carrier_min_hz, settings.carrier_max_hz)

    def track(self, reading: SpectrumReading) -> CarrierReading:
        return CarrierReading(
            samples=tuple(self._detect_peak(spectrum) for spectrum in reading.spectrums)
        )

    def _detect_peak(self, spectrum: ToneSpectrum) -> CarrierSample:
        peak = self._window.loudest(spectrum)
        return CarrierSample(
            ts=spectrum.ts,
            frequency=peak.frequency,
            magnitude=peak.magnitude,
        )
