from morse_decoder.config import SpectrumLimiterSettings
from morse_decoder.pipeline.dto import ToneMagnitude, ToneSpectrum
from morse_decoder.pipeline.stages.spectrum_limiter.interface import SpectrumLimiter


class StaticSpectrumLimiter(SpectrumLimiter):
    """Holds one band, fixed by configuration, over every spectrum it is given."""

    def __init__(self, settings: SpectrumLimiterSettings) -> None:
        self._min_hz = settings.min_hz
        self._max_hz = settings.max_hz

    def transform(self, spectrum: ToneSpectrum) -> ToneSpectrum:
        tones = tuple(tone for tone in spectrum.magnitudes if self._covers(tone))
        if not tones:
            raise ValueError(f"no spectrum bin in {self._min_hz}..{self._max_hz} Hz")
        return ToneSpectrum(ts=spectrum.ts, magnitudes=tones)

    def _covers(self, tone: ToneMagnitude) -> bool:
        return self._min_hz <= tone.frequency <= self._max_hz
