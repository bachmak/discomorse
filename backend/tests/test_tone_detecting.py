"""The pipeline wires the keying stages up and feeds each of them one spectrum."""

import pytest
from carrier_fixtures import (
    ANALYZER_SETTINGS,
    KEYED,
    LOCK_SECONDS,
    SpectrumTimeline,
    spectrum,
)
from key_fixtures import flags
from recording_fixtures import (
    RecordingCarrierSource,
    RecordingKeyingDebouncer,
    RecordingKeyingDetector,
    RecordingNoiseEstimator,
    recording_stages,
)
from tone_detecting_fixtures import ToneDetecting, detect, tone_detecting

from morse_decoder.config import PipelineSettings
from morse_decoder.pipeline.dto import CarrierNoiseSample, ToneSample, ToneSpectrum
from morse_decoder.pipeline.stages.carrier_source.peak_carrier_source import (
    PeakCarrierSource,
)
from morse_decoder.pipeline.stages.keying_debouncer.timed_keying_debouncer import (
    TimedKeyingDebouncer,
)
from morse_decoder.pipeline.stages.keying_detector.adaptive_keying_detector import (
    AdaptiveKeyingDetector,
)
from morse_decoder.pipeline.stages.noise_estimator.percentile_noise_estimator import (
    PercentileNoiseEstimator,
)
from morse_decoder.pipeline.stages.spectrum_limiter.static_spectrum_limiter import (
    StaticSpectrumLimiter,
)

_LOUD = 0.9
_OUT_OF_BAND = {100.0: _LOUD * 2}
_STREAM = SpectrumTimeline().hold(KEYED, LOCK_SECONDS * 4).build()


@pytest.fixture(name="recording")
def recording_fixture(monkeypatch: pytest.MonkeyPatch) -> ToneDetecting:
    return recording_stages(monkeypatch)


def _settings(**names: str) -> PipelineSettings:
    """Pipeline settings that name one stage that no catalog knows."""
    return PipelineSettings(
        spectrum_analyzer_settings=ANALYZER_SETTINGS,
        **names,  # type: ignore[arg-type]  # every stage name is a plain str
    )


def _reading_stages(
    detecting: ToneDetecting,
) -> tuple[RecordingCarrierSource, RecordingNoiseEstimator]:
    return (
        detecting.stage("carrier_source", RecordingCarrierSource),
        detecting.stage("noise_estimator", RecordingNoiseEstimator),
    )


def _keying_stage(detecting: ToneDetecting) -> RecordingKeyingDetector:
    return detecting.stage("keying_detector", RecordingKeyingDetector)


def _debouncing_stage(detecting: ToneDetecting) -> RecordingKeyingDebouncer:
    return detecting.stage("keying_debouncer", RecordingKeyingDebouncer)


def _reported_keys(reported: list[ToneSample]) -> tuple[bool, ...]:
    return flags(tuple(reported))


def _seen_by_reading_stages(
    detecting: ToneDetecting,
) -> tuple[list[ToneSpectrum], ...]:
    return tuple(stage.seen for stage in _reading_stages(detecting))


def test_the_pipeline_builds_the_stages_the_settings_name() -> None:
    detecting = tone_detecting()

    assert detecting.stage("spectrum_limiter", StaticSpectrumLimiter)
    assert detecting.stage("carrier_source", PeakCarrierSource)
    assert detecting.stage("noise_estimator", PercentileNoiseEstimator)
    assert detecting.stage("keying_detector", AdaptiveKeyingDetector)
    assert detecting.stage("keying_debouncer", TimedKeyingDebouncer)


@pytest.mark.parametrize(
    "settings, message",
    [
        pytest.param(
            _settings(spectrum_limiter="missing"),
            "Unknown spectrum limiter: 'missing'",
            id="spectrum-limiter",
        ),
        pytest.param(
            _settings(carrier_source="missing"),
            "Unknown carrier source: 'missing'",
            id="carrier-source",
        ),
        pytest.param(
            _settings(noise_estimator="missing"),
            "Unknown noise estimator: 'missing'",
            id="noise-estimator",
        ),
        pytest.param(
            _settings(keying_detector="missing"),
            "Unknown keying detector: 'missing'",
            id="keying-detector",
        ),
        pytest.param(
            _settings(keying_debouncer="missing"),
            "Unknown keying debouncer: 'missing'",
            id="keying-debouncer",
        ),
    ],
)
def test_an_unknown_stage_name_is_rejected(
    settings: PipelineSettings, message: str
) -> None:
    with pytest.raises(KeyError, match=message):
        tone_detecting(settings)


async def test_every_spectrum_yields_one_sample_stamped_with_its_own_time() -> None:
    samples = await detect(_STREAM)

    assert tuple(sample.ts for sample in samples) == tuple(one.ts for one in _STREAM)


async def test_a_reading_without_spectrums_reports_nothing() -> None:
    assert await detect(()) == ()


@pytest.mark.parametrize(
    "bins",
    [
        pytest.param({100.0: _LOUD}, id="all-bins-below-the-band"),
        pytest.param({2_000.0: _LOUD}, id="all-bins-above-the-band"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
async def test_a_spectrum_missing_the_band_is_rejected(
    bins: dict[float, float],
) -> None:
    with pytest.raises(ValueError, match="no spectrum bin"):
        await detect((spectrum(bins),))


async def test_both_reading_stages_see_every_spectrum(recording: ToneDetecting) -> None:
    spectrums = SpectrumTimeline().add(_OUT_OF_BAND | KEYED, count=3).build()

    await recording.read(spectrums)

    for seen in _seen_by_reading_stages(recording):
        assert [one.ts for one in seen] == [one.ts for one in spectrums]


async def test_both_reading_stages_only_see_the_bins_the_limiter_kept(
    recording: ToneDetecting,
) -> None:
    spectrums = SpectrumTimeline().add(_OUT_OF_BAND | KEYED, count=3).build()

    await recording.read(spectrums)

    for seen in _seen_by_reading_stages(recording):
        assert {tone.frequency for one in seen for tone in one.magnitudes} == set(KEYED)


async def test_the_stages_keep_their_state_across_readings(
    recording: ToneDetecting,
) -> None:
    await recording.read(_STREAM[:3])
    await recording.read(_STREAM[3:])

    for seen in _seen_by_reading_stages(recording):
        assert len(seen) == len(_STREAM)

    assert len(_keying_stage(recording).seen) == len(_STREAM)
    assert len(_debouncing_stage(recording).seen) == len(_STREAM)


async def test_the_keying_stage_reads_what_the_other_two_reported(
    recording: ToneDetecting,
) -> None:
    await recording.read(_STREAM)

    carrier_source, noise_estimator = _reading_stages(recording)
    assert _keying_stage(recording).seen == [
        CarrierNoiseSample(carrier=carrier, noise=noise)
        for carrier, noise in zip(
            carrier_source.reported, noise_estimator.reported, strict=True
        )
    ]


async def test_the_debouncing_stage_reads_the_key_stamped_with_its_spectrums_time(
    recording: ToneDetecting,
) -> None:
    await recording.read(_STREAM)

    seen = _debouncing_stage(recording).seen
    assert seen == _keying_stage(recording).reported
    assert [one.ts for one in seen] == [one.ts for one in _STREAM]


async def test_the_line_reports_the_key_the_debouncing_stage_settled_on(
    recording: ToneDetecting,
) -> None:
    read = flags(await recording.read(_STREAM))

    assert read == _reported_keys(_debouncing_stage(recording).reported)
    assert read != _reported_keys(_keying_stage(recording).reported)
