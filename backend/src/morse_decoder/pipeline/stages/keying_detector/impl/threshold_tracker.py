from morse_decoder.config import KeyingDetectorSettings
from morse_decoder.pipeline.dto import NoiseSample
from morse_decoder.pipeline.stages.keying_detector.dto import KeyingThresholds


class AsymmetricEma:
    """EMA that follows a rise at one rate and a fall at another."""

    def __init__(self, rise_alpha: float, fall_alpha: float) -> None:
        self._rise_alpha = rise_alpha
        self._fall_alpha = fall_alpha
        self._level: float | None = None

    def update(self, value: float) -> float:
        self._level = self._next_level(value)
        return self._level

    def _next_level(self, value: float) -> float:
        if self._level is None:
            return value
        alpha = self._rise_alpha if value > self._level else self._fall_alpha
        return self._level + alpha * (value - self._level)


class ThresholdTracker:
    """Holds the keying thresholds a fixed way above the noise floor it follows.

    The floor is followed asymmetrically: noise that rises is believed sooner than
    noise that fades, so a burst lifts the thresholds at once while a lull lets
    them back down slowly — the key is harder to fool than it is to lose.
    """

    def __init__(self, settings: KeyingDetectorSettings) -> None:
        self._floor = AsymmetricEma(
            rise_alpha=settings.threshold_rise_alpha,
            fall_alpha=settings.threshold_fall_alpha,
        )
        self._on_factor = settings.threshold_on_factor
        self._off_factor = settings.threshold_off_factor

    def update(self, noise: NoiseSample) -> KeyingThresholds:
        floor = self._floor.update(noise.noise)
        return KeyingThresholds(
            on=floor * self._on_factor, off=floor * self._off_factor
        )
