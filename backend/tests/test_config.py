import pytest
from pydantic import ValidationError

from morse_decoder.config import (
    AudioSettings,
    KeyingDebouncerSettings,
    KeyingDetectorSettings,
    PipelineSettings,
    Settings,
    SpectrumAnalyzerSettings,
    SpectrumLimiterSettings,
)


def _settings(audio_rate: int, analyzer_rate: int) -> Settings:
    return Settings(
        audio=AudioSettings(sample_rate=audio_rate),
        pipeline=PipelineSettings(
            spectrum_analyzer_settings=SpectrumAnalyzerSettings(
                sample_rate=analyzer_rate
            )
        ),
    )


@pytest.mark.parametrize(
    "sample_rate",
    [
        pytest.param(8_000, id="default-rate"),
        pytest.param(16_000, id="raised-rate"),
    ],
)
def test_settings_accept_agreeing_sample_rates(sample_rate: int) -> None:
    settings = _settings(sample_rate, sample_rate)

    assert settings.pipeline.spectrum_analyzer_settings.sample_rate == sample_rate


@pytest.mark.parametrize(
    "audio_rate, analyzer_rate",
    [
        pytest.param(16_000, 8_000, id="analyzer-lags-behind"),
        pytest.param(8_000, 44_100, id="analyzer-runs-ahead"),
    ],
)
def test_settings_reject_disagreeing_sample_rates(
    audio_rate: int, analyzer_rate: int
) -> None:
    with pytest.raises(ValidationError, match="must equal"):
        _settings(audio_rate, analyzer_rate)


@pytest.mark.parametrize(
    "min_hz, max_hz",
    [
        pytest.param(1_200.0, 400.0, id="band-inverted"),
        pytest.param(700.0, 700.0, id="band-empty"),
    ],
)
def test_limiter_settings_reject_a_band_that_never_opens(
    min_hz: float, max_hz: float
) -> None:
    with pytest.raises(ValidationError, match="must be below"):
        SpectrumLimiterSettings(min_hz=min_hz, max_hz=max_hz)


@pytest.mark.parametrize(
    "on_factor, off_factor",
    [
        pytest.param(1.5, 3.0, id="band-inverted"),
        pytest.param(3.0, 3.0, id="band-empty"),
    ],
)
def test_keying_detector_settings_reject_a_keying_band_that_never_opens(
    on_factor: float, off_factor: float
) -> None:
    with pytest.raises(ValidationError, match="must be below"):
        KeyingDetectorSettings(
            threshold_on_factor=on_factor, threshold_off_factor=off_factor
        )


@pytest.mark.parametrize(
    "rise_seconds, fall_seconds",
    [
        pytest.param(0.02, 0.004, id="delays-swapped"),
        pytest.param(0.01, 0.009, id="the-key-lifts-sooner-than-it-falls"),
    ],
)
def test_keying_debouncer_settings_reject_a_debouncer_that_lifts_the_key_too_readily(
    rise_seconds: float, fall_seconds: float
) -> None:
    with pytest.raises(ValidationError, match="must not exceed"):
        KeyingDebouncerSettings(
            debounce_rise_seconds=rise_seconds, debounce_fall_seconds=fall_seconds
        )


def test_default_settings_agree_on_the_sample_rate() -> None:
    settings = Settings()

    assert (
        settings.audio.sample_rate
        == settings.pipeline.spectrum_analyzer_settings.sample_rate
    )
