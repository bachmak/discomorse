from dataclasses import dataclass

from morse_decoder.pipeline.dto import ToneMagnitude, ToneSpectrum


@dataclass(frozen=True)
class FrequencyWindow:
    """The band the carrier is looked for in; bounds are inclusive."""

    min_hz: float
    max_hz: float

    def loudest(self, spectrum: ToneSpectrum) -> ToneMagnitude:
        return max(self._inside(spectrum), key=lambda tone: tone.magnitude)

    def _inside(self, spectrum: ToneSpectrum) -> tuple[ToneMagnitude, ...]:
        inside = tuple(tone for tone in spectrum.magnitudes if self._contains(tone))
        if not inside:
            raise ValueError(
                f"no spectrum bin falls into {self.min_hz}..{self.max_hz} Hz"
            )
        return inside

    def _contains(self, tone: ToneMagnitude) -> bool:
        return self.min_hz <= tone.frequency <= self.max_hz
