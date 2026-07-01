### THIS FILE IS FOR TESTING PURPOSES ONLY. DO NOT COPY OR IMPORT
### ANYTHING FROM THIS FILE INTO PRODUCTION CODE. ###


import pytest

from morse_decoder.config import (
    PipelineSettings,
    SpectrumAnalyzerSettings,
    ToneDetectorSettings,
)
from morse_decoder.pipeline import factory
from morse_decoder.pipeline.dto import PcmChunk, SpectrumReading, ToneReading
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.tone_detector.interface import ToneDetector


class _FakeAnalyzer(SpectrumAnalyzer):
    """Stand-in spectrum analyzer that records the settings it was built with."""

    def __init__(self, settings: SpectrumAnalyzerSettings) -> None:
        self._settings = settings

    async def process(self, chunk: PcmChunk) -> SpectrumReading:
        return SpectrumReading(spectrums=())


class _FakeDetector(ToneDetector):
    """Stand-in tone detector that records the settings it was built with."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings

    async def process(self, reading: SpectrumReading) -> ToneReading:
        return ToneReading(samples=())


def test_resolve_returns_registered_class() -> None:
    catalog: dict[str, type[ToneDetector]] = {"fake": _FakeDetector}

    assert factory._resolve(catalog, "fake", "tone detector") is _FakeDetector


@pytest.mark.parametrize(
    "catalog",
    [
        pytest.param({}, id="empty-catalog"),
        pytest.param({"other": _FakeDetector}, id="non-empty-catalog"),
    ],
)
def test_resolve_unknown_name_raises(catalog: dict[str, type[ToneDetector]]) -> None:
    with pytest.raises(KeyError, match="Unknown tone detector: 'missing'"):
        factory._resolve(catalog, "missing", "tone detector")


def test_build_passes_typed_settings_to_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(factory._TONE_DETECTORS, "fake", _FakeDetector)
    tone_settings = ToneDetectorSettings()
    settings = PipelineSettings(
        tone_detector="fake", tone_detector_settings=tone_settings
    )

    detector = factory._build_tone_detector(settings)

    assert isinstance(detector, _FakeDetector)
    assert detector._settings is tone_settings


def test_build_passes_typed_settings_to_analyzer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(factory._SPECTRUM_ANALYZERS, "fake", _FakeAnalyzer)
    analyzer_settings = SpectrumAnalyzerSettings()
    settings = PipelineSettings(
        spectrum_analyzer="fake", spectrum_analyzer_settings=analyzer_settings
    )

    analyzer = factory._build_spectrum_analyzer(settings)

    assert isinstance(analyzer, _FakeAnalyzer)
    assert analyzer._settings is analyzer_settings
