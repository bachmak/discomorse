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
    KeyingSample,
    NoiseSample,
    Tone,
)
from morse_decoder.pipeline.stages.tone_detector.impl.keying_detector import (
    AdaptiveKeyingDetector,
    KeyingDetector,
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


class _RecordingNoiseEstimator(NoiseEstimator):
    """Stand-in estimator that keeps every spectrum the detector hands it."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[ToneSpectrum] = []
        self.reported: list[NoiseSample] = []

    def estimate(self, spectrum: ToneSpectrum) -> NoiseSample:
        self.seen.append(spectrum)
        self.reported.append(NoiseSample(noise=float(len(self.seen))))
        return self.reported[-1]


class _RecordingKeyingDetector(KeyingDetector):
    """Stand-in detector that keeps every pair the detector hands it.

    It always reports a keyed line: the samples leaving the stage must stay
    key-up all the same, until the substage's output is wired to them.
    """

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings
        self.seen: list[tuple[CarrierSample, NoiseSample]] = []

    def detect(self, carrier: CarrierSample, noise: NoiseSample) -> KeyingSample:
        self.seen.append((carrier, noise))
        return KeyingSample(is_on=True)


@pytest.fixture
def recording_detector(monkeypatch: pytest.MonkeyPatch) -> SpectralToneDetector:
    monkeypatch.setitem(
        tone_detector._CARRIER_SOURCES, "recording", _RecordingCarrierSource
    )
    monkeypatch.setitem(
        tone_detector._NOISE_ESTIMATORS, "recording", _RecordingNoiseEstimator
    )
    monkeypatch.setitem(
        tone_detector._KEYING_DETECTORS, "recording", _RecordingKeyingDetector
    )
    return SpectralToneDetector(
        ToneDetectorSettings(
            carrier_source="recording",
            noise_estimator="recording",
            keying_detector="recording",
        )
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
    assert isinstance(detector._keying_detector, AdaptiveKeyingDetector)


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
        pytest.param(
            ToneDetectorSettings(keying_detector="missing"),
            "Unknown keying detector: 'missing'",
            id="keying-detector",
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


def _reading_substages(
    detector: SpectralToneDetector,
) -> tuple[_RecordingCarrierSource, _RecordingNoiseEstimator]:
    carrier_source = detector._carrier_source
    noise_estimator = detector._noise_estimator
    assert isinstance(carrier_source, _RecordingCarrierSource)
    assert isinstance(noise_estimator, _RecordingNoiseEstimator)
    return carrier_source, noise_estimator


def _keying_substage(detector: SpectralToneDetector) -> _RecordingKeyingDetector:
    keying_detector = detector._keying_detector
    assert isinstance(keying_detector, _RecordingKeyingDetector)
    return keying_detector


def _seen_by_substages(
    detector: SpectralToneDetector,
) -> tuple[list[ToneSpectrum], ...]:
    return tuple(substage.seen for substage in _reading_substages(detector))


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

    assert len(_keying_substage(recording_detector).seen) == len(_STREAM)


async def test_the_keying_substage_reads_what_the_other_two_reported(
    recording_detector: SpectralToneDetector,
) -> None:
    await _process(recording_detector, _STREAM)

    carrier_source, noise_estimator = _reading_substages(recording_detector)
    assert _keying_substage(recording_detector).seen == list(
        zip(carrier_source.reported, noise_estimator.reported, strict=True)
    )


async def test_the_key_the_substage_reads_stays_off_the_stages_output(
    recording_detector: SpectralToneDetector,
) -> None:
    samples = await _process(recording_detector, _STREAM)

    assert _keying_substage(recording_detector).seen
    assert not any(sample.on for sample in samples)
