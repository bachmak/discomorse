"""Stand-in stages that keep whatever the pipeline hands them.

Each double reports something the next stage in the chain can be caught
holding, so a test can tell what was passed on from what was merely read.
"""

import datetime

import pytest
from carrier_fixtures import ANALYZER_SETTINGS
from tone_detecting_fixtures import ToneDetecting, tone_detecting

from morse_decoder.config import (
    CarrierSourceSettings,
    KeyingDebouncerSettings,
    KeyingDetectorSettings,
    NoiseEstimatorSettings,
    PipelineSettings,
)
from morse_decoder.pipeline import factory
from morse_decoder.pipeline.dto import (
    CarrierSample,
    KeyingSample,
    NoiseSample,
    Tone,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource
from morse_decoder.pipeline.stages.keying_debouncer.interface import KeyingDebouncer
from morse_decoder.pipeline.stages.keying_detector.interface import KeyingDetector
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator

NAME = "recording"


class RecordingCarrierSource(CarrierSource):
    """Stand-in source that keeps every spectrum the pipeline hands it.

    Each sample it reports is stamped with its spectrum's time, so what the
    keying stage was handed can be told apart reading by reading.
    """

    def __init__(self, settings: CarrierSourceSettings) -> None:
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
    """Stand-in estimator that keeps every spectrum the pipeline hands it."""

    def __init__(self, settings: NoiseEstimatorSettings) -> None:
        self._settings = settings
        self.seen: list[ToneSpectrum] = []
        self.reported: list[NoiseSample] = []

    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        self.seen.append(spectrum)
        self.reported.append(NoiseSample(noise=float(len(self.seen))))
        return self.reported[-1]


class RecordingKeyingDetector(KeyingDetector):
    """Stand-in detector that keeps every pair the pipeline hands it.

    It always reports a keyed line, so the key that leaves the stages can be told
    apart from the one the stage behind it settled on.
    """

    def __init__(self, settings: KeyingDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[tuple[CarrierSample, NoiseSample]] = []
        self.reported: list[KeyingSample] = []

    def detect(self, carrier: CarrierSample, noise: NoiseSample) -> KeyingSample:
        self.seen.append((carrier, noise))
        self.reported.append(KeyingSample(is_on=True))
        return self.reported[-1]


class RecordingKeyingDebouncer(KeyingDebouncer):
    """Stand-in debouncer that keeps every key the pipeline hands it, and when.

    It settles on a key of its own that swings from reading to reading, so what
    leaves the stages can only be read off this one, the last of the four.
    """

    def __init__(self, settings: KeyingDebouncerSettings) -> None:
        self._settings = settings
        self.seen: list[tuple[KeyingSample, datetime.datetime]] = []
        self.reported: list[KeyingSample] = []

    def debounce(self, sample: KeyingSample, ts: datetime.datetime) -> KeyingSample:
        self.seen.append((sample, ts))
        self.reported.append(KeyingSample(is_on=len(self.seen) % 2 == 0))
        return self.reported[-1]


def recording_stages(monkeypatch: pytest.MonkeyPatch) -> ToneDetecting:
    """Tone detecting out of nothing but the recording stages."""
    monkeypatch.setitem(factory._CARRIER_SOURCES, NAME, RecordingCarrierSource)
    monkeypatch.setitem(factory._NOISE_ESTIMATORS, NAME, RecordingNoiseEstimator)
    monkeypatch.setitem(factory._KEYING_DETECTORS, NAME, RecordingKeyingDetector)
    monkeypatch.setitem(factory._KEYING_DEBOUNCERS, NAME, RecordingKeyingDebouncer)
    return tone_detecting(
        PipelineSettings(
            spectrum_analyzer_settings=ANALYZER_SETTINGS,
            carrier_source=NAME,
            noise_estimator=NAME,
            keying_detector=NAME,
            keying_debouncer=NAME,
        )
    )
