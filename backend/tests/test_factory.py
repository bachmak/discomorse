### THIS FILE IS FOR TESTING PURPOSES ONLY. DO NOT COPY OR IMPORT
### ANYTHING FROM THIS FILE INTO PRODUCTION CODE. ###


import pytest

from morse_decoder.config import (
    CarrierSourceSettings,
    PipelineSettings,
    SpectrumAnalyzerSettings,
)
from morse_decoder.pipeline import factory
from morse_decoder.pipeline.dto import (
    CarrierSample,
    PcmChunk,
    SpectrumReading,
    Tone,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)

_CATALOGS = [
    pytest.param(factory._SPECTRUM_ANALYZERS, id="spectrum-analyzers"),
    pytest.param(factory._SPECTRUM_LIMITERS, id="spectrum-limiters"),
    pytest.param(factory._CARRIER_SOURCES, id="carrier-sources"),
    pytest.param(factory._NOISE_ESTIMATORS, id="noise-estimators"),
    pytest.param(factory._KEYING_DETECTORS, id="keying-detectors"),
    pytest.param(factory._KEYING_DEBOUNCERS, id="keying-debouncers"),
    pytest.param(factory._TIMING_DECODERS, id="timing-decoders"),
    pytest.param(factory._INTERPRETERS, id="interpreters"),
]


class _FakeAnalyzer(SpectrumAnalyzer):
    """Stand-in spectrum analyzer that records the settings it was built with."""

    def __init__(self, settings: SpectrumAnalyzerSettings) -> None:
        self._settings = settings

    async def process(self, chunk: PcmChunk) -> SpectrumReading:
        return SpectrumReading(spectrums=())


class _FakeCarrierSource(CarrierSource):
    """Stand-in carrier source that records the settings it was built with."""

    def __init__(self, settings: CarrierSourceSettings) -> None:
        self._settings = settings

    def track(self, spectrum: ToneSpectrum) -> CarrierSample:
        return CarrierSample(tone=Tone.empty(), is_locked=False)


def test_resolve_returns_registered_class() -> None:
    catalog = {"fake": _FakeCarrierSource}

    assert factory._resolve(catalog, "fake", "carrier source") is _FakeCarrierSource


@pytest.mark.parametrize(
    "catalog",
    [
        pytest.param({}, id="empty-catalog"),
        pytest.param({"other": _FakeCarrierSource}, id="non-empty-catalog"),
    ],
)
def test_resolve_unknown_name_raises(
    catalog: dict[str, type[_FakeCarrierSource]],
) -> None:
    with pytest.raises(KeyError, match="Unknown carrier source: 'missing'"):
        factory._resolve(catalog, "missing", "carrier source")


def test_build_passes_typed_settings_to_plugin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(factory._CARRIER_SOURCES, "fake", _FakeCarrierSource)
    carrier_settings = CarrierSourceSettings()
    settings = PipelineSettings(
        carrier_source="fake", carrier_source_settings=carrier_settings
    )

    carrier_source = factory._build_carrier_source(settings)

    assert isinstance(carrier_source, _FakeCarrierSource)
    assert carrier_source._settings is carrier_settings


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


@pytest.mark.parametrize("catalog", _CATALOGS)
def test_every_stage_is_registered_under_its_class_name(
    catalog: dict[str, type],
) -> None:
    assert catalog
    assert all(name == stage.__name__ for name, stage in catalog.items())


def test_default_settings_build_the_stft_analyzer() -> None:
    analyzer = factory._build_spectrum_analyzer(PipelineSettings())

    assert isinstance(analyzer, STFTSpectrumAnalyzer)
