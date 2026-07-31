"""Stand-in substages that keep whatever the tone detector hands them.

Each double reports something the next substage in the chain can be caught
holding, so a test can tell what was passed on from what was merely read.
"""

import datetime

import pytest

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector import tone_detector
from morse_decoder.pipeline.stages.tone_detector.impl.carrier_source import (
    CarrierSource,
)
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    KeyingSample,
    NoiseSample,
    Tone,
)
from morse_decoder.pipeline.stages.tone_detector.impl.keying_debouncer import (
    KeyingDebouncer,
)
from morse_decoder.pipeline.stages.tone_detector.impl.keying_detector import (
    KeyingDetector,
)
from morse_decoder.pipeline.stages.tone_detector.impl.noise_estimator import (
    NoiseEstimator,
)
from morse_decoder.pipeline.stages.tone_detector.tone_detector import (
    SpectralToneDetector,
)

NAME = "recording"


class RecordingCarrierSource(CarrierSource):
    """Stand-in source that keeps every spectrum the detector hands it.

    Each sample it reports is stamped with its spectrum's time, so what the
    keying substage was handed can be told apart reading by reading.
    """

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[ToneSpectrum] = []
        self.reported: list[CarrierSample] = []

    def track(self, spectrum: ToneSpectrum) -> CarrierSample:
        self.seen.append(spectrum)
        self.reported.append(
            CarrierSample(tone=Tone.empty().with_ts(spectrum.ts), is_locked=False)
        )
        return self.reported[-1]


class RecordingNoiseEstimator(NoiseEstimator):
    """Stand-in estimator that keeps every spectrum the detector hands it."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[ToneSpectrum] = []
        self.reported: list[NoiseSample] = []

    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        self.seen.append(spectrum)
        self.reported.append(NoiseSample(noise=float(len(self.seen))))
        return self.reported[-1]


class RecordingKeyingDetector(KeyingDetector):
    """Stand-in detector that keeps every pair the detector hands it.

    It always reports a keyed line: the samples leaving the stage must stay
    key-up all the same, until the substage's output is wired to them.
    """

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[tuple[CarrierSample, NoiseSample]] = []
        self.reported: list[KeyingSample] = []

    def detect(self, carrier: CarrierSample, noise: NoiseSample) -> KeyingSample:
        self.seen.append((carrier, noise))
        self.reported.append(KeyingSample(is_on=True))
        return self.reported[-1]


class RecordingKeyingDebouncer(KeyingDebouncer):
    """Stand-in debouncer that keeps every key the detector hands it, and when."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[tuple[KeyingSample, datetime.datetime]] = []

    def debounce(self, sample: KeyingSample, ts: datetime.datetime) -> KeyingSample:
        self.seen.append((sample, ts))
        return KeyingSample(is_on=True)


def recording_detector(monkeypatch: pytest.MonkeyPatch) -> SpectralToneDetector:
    """A tone detector built out of nothing but the recording substages."""
    monkeypatch.setitem(tone_detector._CARRIER_SOURCES, NAME, RecordingCarrierSource)
    monkeypatch.setitem(tone_detector._NOISE_ESTIMATORS, NAME, RecordingNoiseEstimator)
    monkeypatch.setitem(tone_detector._KEYING_DETECTORS, NAME, RecordingKeyingDetector)
    monkeypatch.setitem(
        tone_detector._KEYING_DEBOUNCERS, NAME, RecordingKeyingDebouncer
    )
    return SpectralToneDetector(
        ToneDetectorSettings(
            carrier_source=NAME,
            noise_estimator=NAME,
            keying_detector=NAME,
            keying_debouncer=NAME,
        )
    )
