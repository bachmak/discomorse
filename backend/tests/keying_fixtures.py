"""Builders for the carriers, floors and readers the keying tests drive.

The keying substage never sees a spectrum: it reads one carrier level against
one noise floor, so a test writes a ``Step`` per reading instead of a bin
dictionary. Levels are named after where they sit relative to the thresholds
the default settings put over ``FLOOR``.
"""

from dataclasses import dataclass, replace

from audio_fixtures import EPOCH
from carrier_fixtures import CARRIER_HZ, SETTINGS, WINDOW, source
from noise_fixtures import estimator

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    FrequencyWindow,
    KeyingSample,
    KeyingThresholds,
    NoiseSample,
    Tone,
)
from morse_decoder.pipeline.stages.tone_detector.impl.helpers import limit_to_window
from morse_decoder.pipeline.stages.tone_detector.impl.keying_detector import (
    AdaptiveKeyingDetector,
)
from morse_decoder.pipeline.stages.tone_detector.impl.threshold_tracker import (
    ThresholdTracker,
)

RISE_ALPHA = SETTINGS.threshold_rise_alpha
FALL_ALPHA = SETTINGS.threshold_fall_alpha
ON_FACTOR = SETTINGS.threshold_on_factor
OFF_FACTOR = SETTINGS.threshold_off_factor

FLOOR = 0.02
OVER_ON = FLOOR * ON_FACTOR * 2
IN_BAND = FLOOR * (ON_FACTOR + OFF_FACTOR) / 2
UNDER_OFF = FLOOR * OFF_FACTOR / 2


@dataclass(frozen=True)
class Step:
    """One reading as the keying detector sees it: a carrier over a noise floor."""

    magnitude: float
    floor: float = FLOOR
    is_locked: bool = True

    def carrier(self) -> CarrierSample:
        return CarrierSample(
            tone=Tone(frequency=CARRIER_HZ, magnitude=self.magnitude, ts=EPOCH),
            is_locked=self.is_locked,
        )

    def noise(self) -> NoiseSample:
        return NoiseSample(noise=self.floor)


def steps(
    magnitudes: tuple[float, ...], floor: float = FLOOR, is_locked: bool = True
) -> tuple[Step, ...]:
    """One step per magnitude, all of them over the same floor."""
    return tuple(Step(magnitude, floor, is_locked) for magnitude in magnitudes)


def steps_over(
    magnitude: float, floors: tuple[float, ...], is_locked: bool = True
) -> tuple[Step, ...]:
    """One step per floor, all of them under the same carrier."""
    return tuple(Step(magnitude, floor, is_locked) for floor in floors)


def unlocked(readings: tuple[Step, ...]) -> tuple[Step, ...]:
    return tuple(replace(step, is_locked=False) for step in readings)


def detector(settings: ToneDetectorSettings | None = None) -> AdaptiveKeyingDetector:
    return AdaptiveKeyingDetector(settings or SETTINGS)


def detect(
    readings: tuple[Step, ...],
    *,
    keying_detector: AdaptiveKeyingDetector | None = None,
) -> tuple[KeyingSample, ...]:
    """Feed ``readings`` to one detector the way the tone detector would."""
    reader = keying_detector or detector()
    return tuple(reader.detect(step.carrier(), step.noise()) for step in readings)


def keys(samples: tuple[KeyingSample, ...]) -> tuple[bool, ...]:
    return tuple(sample.is_on for sample in samples)


def keyed(
    readings: tuple[Step, ...],
    *,
    keying_detector: AdaptiveKeyingDetector | None = None,
) -> tuple[bool, ...]:
    """The key as one detector reads it off ``readings``."""
    return keys(detect(readings, keying_detector=keying_detector))


def key_off(
    spectrums: tuple[ToneSpectrum, ...], window: FrequencyWindow = WINDOW
) -> tuple[KeyingSample, ...]:
    """Read the key off spectrums the way the tone detector wires the substages."""
    carrier_source, noise_estimator, keying_detector = source(), estimator(), detector()
    return tuple(
        keying_detector.detect(
            carrier_source.track(windowed), noise_estimator.estimate(windowed)
        )
        for windowed in (limit_to_window(spectrum, window) for spectrum in spectrums)
    )


def tracker(settings: ToneDetectorSettings | None = None) -> ThresholdTracker:
    return ThresholdTracker(settings or SETTINGS)


def track(
    floors: tuple[float, ...], *, threshold_tracker: ThresholdTracker | None = None
) -> tuple[KeyingThresholds, ...]:
    """Feed ``floors`` to one tracker the way the keying detector would."""
    reader = threshold_tracker or tracker()
    return tuple(reader.update(NoiseSample(noise=floor)) for floor in floors)


def ons(bands: tuple[KeyingThresholds, ...]) -> tuple[float, ...]:
    return tuple(band.on for band in bands)


def offs(bands: tuple[KeyingThresholds, ...]) -> tuple[float, ...]:
    return tuple(band.off for band in bands)
