"""Builders for the carriers, floors and readers the keying tests drive.

The keying stage never sees a spectrum: it reads one carrier level against one
noise floor, so a test writes a ``Step`` per reading instead of a bin
dictionary. Levels are named after where they sit relative to the thresholds
the default settings put over ``FLOOR``.
"""

from dataclasses import dataclass, replace

from audio_fixtures import EPOCH
from carrier_fixtures import CARRIER_HZ, source
from limiter_fixtures import limit
from noise_fixtures import estimator

from morse_decoder.config import KeyingDetectorSettings
from morse_decoder.pipeline.dto import (
    CarrierSample,
    KeyingSample,
    NoiseSample,
    Tone,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.keying_detector.adaptive_keying_detector import (
    AdaptiveKeyingDetector,
)
from morse_decoder.pipeline.stages.keying_detector.dto import KeyingThresholds
from morse_decoder.pipeline.stages.keying_detector.impl.threshold_tracker import (
    ThresholdTracker,
)

SETTINGS = KeyingDetectorSettings()
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


def detector(settings: KeyingDetectorSettings | None = None) -> AdaptiveKeyingDetector:
    return AdaptiveKeyingDetector(settings or SETTINGS)


def detect(
    readings: tuple[Step, ...],
    *,
    keying_detector: AdaptiveKeyingDetector | None = None,
) -> tuple[KeyingSample, ...]:
    """Feed ``readings`` to one detector the way the pipeline would."""
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


async def key_off(spectrums: tuple[ToneSpectrum, ...]) -> tuple[KeyingSample, ...]:
    """Read the key off spectrums the way the pipeline wires the four stages."""
    carrier_source, noise_estimator, keying_detector = source(), estimator(), detector()
    return tuple(
        keying_detector.detect(
            carrier_source.track(limited), noise_estimator.estimate(limited)
        )
        for limited in await limit(spectrums)
    )


def tracker(settings: KeyingDetectorSettings | None = None) -> ThresholdTracker:
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
