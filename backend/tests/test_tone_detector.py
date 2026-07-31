"""The detector wires the substages up and feeds each of them one window at a time."""

import pytest
from carrier_fixtures import KEYED, LOCK_SECONDS, SpectrumTimeline, spectrum

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import (
    SpectrumReading,
    ToneSample,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.tone_detector import tone_detector
from morse_decoder.pipeline.stages.tone_detector.impl.carrier_source import (
    CarrierSource,
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    CarrierSample,
    NoiseSample,
    Tone,
)
from morse_decoder.pipeline.stages.tone_detector.impl.noise_estimator import (
    NoiseEstimator,
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.tone_detector.tone_detector import (
    SpectralToneDetector,
)

_LOUD = 0.9
_STREAM = SpectrumTimeline().hold(KEYED, LOCK_SECONDS * 4).build()


class _RecordingCarrierSource(CarrierSource):
    """Stand-in source that keeps every spectrum the detector hands it."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[ToneSpectrum] = []

    def track(self, spectrum: ToneSpectrum) -> CarrierSample:
        self.seen.append(spectrum)
        return CarrierSample(tone=Tone.empty(), is_locked=False)


class _RecordingNoiseEstimator(NoiseEstimator):
    """Stand-in estimator that keeps every spectrum the detector hands it."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[ToneSpectrum] = []

    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        self.seen.append(spectrum)
        return NoiseSample(noise=0.0)


@pytest.fixture
def recording_detector(monkeypatch: pytest.MonkeyPatch) -> SpectralToneDetector:
    monkeypatch.setitem(
        tone_detector._CARRIER_SOURCES, "recording", _RecordingCarrierSource
    )
    monkeypatch.setitem(
        tone_detector._NOISE_ESTIMATORS, "recording", _RecordingNoiseEstimator
    )
    return SpectralToneDetector(
        ToneDetectorSettings(carrier_source="recording", noise_estimator="recording")
    )


def _detector() -> SpectralToneDetector:
    return SpectralToneDetector(ToneDetectorSettings())


async def _process(
    detector: SpectralToneDetector, spectrums: tuple[ToneSpectrum, ...]
) -> tuple[ToneSample, ...]:
    return (await detector.process(SpectrumReading(spectrums=spectrums))).samples


def test_the_detector_builds_the_substages_the_settings_name() -> None:
    detector = _detector()

    assert isinstance(detector._carrier_source, PeakCarrierSource)
    assert isinstance(detector._noise_estimator, PercentileNoiseEstimator)


@pytest.mark.parametrize(
    "settings, message",
    [
        pytest.param(
            ToneDetectorSettings(carrier_source="missing"),
            "Unknown carrier source: 'missing'",
            id="carrier-source",
        ),
        pytest.param(
            ToneDetectorSettings(noise_estimator="missing"),
            "Unknown noise estimator: 'missing'",
            id="noise-estimator",
        ),
    ],
)
def test_an_unknown_substage_name_is_rejected(
    settings: ToneDetectorSettings, message: str
) -> None:
    with pytest.raises(KeyError, match=message):
        SpectralToneDetector(settings)


async def test_every_spectrum_yields_one_key_up_sample_stamped_with_its_own_time() -> (
    None
):
    samples = await _process(_detector(), _STREAM)

    assert samples == tuple(ToneSample(ts=one.ts, on=False) for one in _STREAM)


async def test_a_reading_without_spectrums_reports_nothing() -> None:
    assert await _process(_detector(), ()) == ()


@pytest.mark.parametrize(
    "bins",
    [
        pytest.param({100.0: _LOUD}, id="all-bins-below-window"),
        pytest.param({2_000.0: _LOUD}, id="all-bins-above-window"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
async def test_a_spectrum_missing_the_window_is_rejected(
    bins: dict[float, float],
) -> None:
    with pytest.raises(ValueError, match="no spectrum bin"):
        await _process(_detector(), (spectrum(bins),))


def _seen_by_substages(
    detector: SpectralToneDetector,
) -> tuple[list[ToneSpectrum], list[ToneSpectrum]]:
    carrier_source = detector._carrier_source
    noise_estimator = detector._noise_estimator
    assert isinstance(carrier_source, _RecordingCarrierSource)
    assert isinstance(noise_estimator, _RecordingNoiseEstimator)
    return carrier_source.seen, noise_estimator.seen


async def test_both_substages_see_every_spectrum_limited_to_the_window(
    recording_detector: SpectralToneDetector,
) -> None:
    spectrums = SpectrumTimeline().add({100.0: _LOUD * 2} | KEYED, count=3).build()

    await _process(recording_detector, spectrums)

    for seen in _seen_by_substages(recording_detector):
        assert [one.ts for one in seen] == [one.ts for one in spectrums]
        assert all(
            100.0 not in [tone.frequency for tone in one.magnitudes] for one in seen
        )


async def test_the_substages_keep_their_state_across_readings(
    recording_detector: SpectralToneDetector,
) -> None:
    await _process(recording_detector, _STREAM[:3])
    await _process(recording_detector, _STREAM[3:])

    for seen in _seen_by_substages(recording_detector):
        assert len(seen) == len(_STREAM)
