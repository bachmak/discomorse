"""The detector wires the substages up and feeds each of them one window at a time."""

import pytest
from carrier_fixtures import KEYED, LOCK_SECONDS, SpectrumTimeline, spectrum
from recording_fixtures import (
    RecordingCarrierSource,
    RecordingKeyingDebouncer,
    RecordingKeyingDetector,
    RecordingNoiseEstimator,
    recording_detector,
)

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import (
    SpectrumReading,
    ToneSample,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.tone_detector.impl.carrier_source import (
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.tone_detector.impl.keying_debouncer import (
    TimedKeyingDebouncer,
)
from morse_decoder.pipeline.stages.tone_detector.impl.keying_detector import (
    AdaptiveKeyingDetector,
)
from morse_decoder.pipeline.stages.tone_detector.impl.noise_estimator import (
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.tone_detector.tone_detector import (
    SpectralToneDetector,
)

_LOUD = 0.9
_STREAM = SpectrumTimeline().hold(KEYED, LOCK_SECONDS * 4).build()


@pytest.fixture(name="recording_detector")
def recording_detector_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> SpectralToneDetector:
    return recording_detector(monkeypatch)


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
    assert isinstance(detector._keying_debouncer, TimedKeyingDebouncer)


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
        pytest.param(
            ToneDetectorSettings(keying_debouncer="missing"),
            "Unknown keying debouncer: 'missing'",
            id="keying-debouncer",
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
) -> tuple[RecordingCarrierSource, RecordingNoiseEstimator]:
    carrier_source = detector._carrier_source
    noise_estimator = detector._noise_estimator
    assert isinstance(carrier_source, RecordingCarrierSource)
    assert isinstance(noise_estimator, RecordingNoiseEstimator)
    return carrier_source, noise_estimator


def _keying_substage(detector: SpectralToneDetector) -> RecordingKeyingDetector:
    keying_detector = detector._keying_detector
    assert isinstance(keying_detector, RecordingKeyingDetector)
    return keying_detector


def _debouncing_substage(detector: SpectralToneDetector) -> RecordingKeyingDebouncer:
    keying_debouncer = detector._keying_debouncer
    assert isinstance(keying_debouncer, RecordingKeyingDebouncer)
    return keying_debouncer


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
    assert len(_debouncing_substage(recording_detector).seen) == len(_STREAM)


async def test_the_keying_substage_reads_what_the_other_two_reported(
    recording_detector: SpectralToneDetector,
) -> None:
    await _process(recording_detector, _STREAM)

    carrier_source, noise_estimator = _reading_substages(recording_detector)
    assert _keying_substage(recording_detector).seen == list(
        zip(carrier_source.reported, noise_estimator.reported, strict=True)
    )


async def test_the_debouncing_substage_reads_the_key_stamped_with_its_spectrums_time(
    recording_detector: SpectralToneDetector,
) -> None:
    await _process(recording_detector, _STREAM)

    keying_detector = _keying_substage(recording_detector)
    assert _debouncing_substage(recording_detector).seen == list(
        zip(keying_detector.reported, [one.ts for one in _STREAM], strict=True)
    )


async def test_the_key_the_substages_read_stays_off_the_stages_output(
    recording_detector: SpectralToneDetector,
) -> None:
    samples = await _process(recording_detector, _STREAM)

    assert _keying_substage(recording_detector).seen
    assert _debouncing_substage(recording_detector).seen
    assert not any(sample.on for sample in samples)
