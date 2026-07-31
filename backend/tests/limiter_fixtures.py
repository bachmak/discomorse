"""Builders for the limiters and spectrums the limiting tests drive.

Spectrums come from ``carrier_fixtures`` — every stage that reads bins reads the
ones this stage leaves behind, so they share one way of writing bins down.
"""

from carrier_fixtures import spectrum

from morse_decoder.config import SpectrumLimiterSettings
from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.spectrum_limiter.static_spectrum_limiter import (
    StaticSpectrumLimiter,
)

SETTINGS = SpectrumLimiterSettings()
MIN_HZ = SETTINGS.min_hz
MAX_HZ = SETTINGS.max_hz


def limiter(min_hz: float = MIN_HZ, max_hz: float = MAX_HZ) -> StaticSpectrumLimiter:
    return StaticSpectrumLimiter(SpectrumLimiterSettings(min_hz=min_hz, max_hz=max_hz))


def limit(
    spectrums: tuple[ToneSpectrum, ...],
    *,
    spectrum_limiter: StaticSpectrumLimiter | None = None,
) -> tuple[ToneSpectrum, ...]:
    """Feed ``spectrums`` to one limiter the way the pipeline would."""
    reader = spectrum_limiter or limiter()
    return tuple(reader.limit(one) for one in spectrums)


def limited(
    bins: dict[float, float],
    at_second: float = 0.0,
    *,
    spectrum_limiter: StaticSpectrumLimiter | None = None,
) -> ToneSpectrum:
    """What one limiter leaves of a single spectrum of ``bins``."""
    return limit((spectrum(bins, at_second),), spectrum_limiter=spectrum_limiter)[0]


def kept(
    bins: dict[float, float],
    *,
    spectrum_limiter: StaticSpectrumLimiter | None = None,
) -> tuple[float, ...]:
    """The frequencies of ``bins`` that survive one limiter."""
    one = limited(bins, spectrum_limiter=spectrum_limiter)
    return tuple(tone.frequency for tone in one.magnitudes)
