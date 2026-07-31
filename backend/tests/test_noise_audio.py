"""The noise floor read off spectrums of synthesized audio, not hand-built bins."""

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import noise_pcm, sine_pcm
from carrier_fixtures import SAMPLE_RATE, analyze
from noise_fixtures import estimate, estimator, noises

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.dto import SpectrumReading

_TONE_HZ = 750.0
_SECONDS = 0.1
_QUIET_NOISE = 0.02
_LOUD_NOISE = 0.1


def _tone(amplitude: float = 0.5) -> npt.NDArray[PCM16.IntType]:
    return sine_pcm(_TONE_HZ, _SECONDS, SAMPLE_RATE, amplitude)


def _noise(amplitude: float) -> npt.NDArray[PCM16.IntType]:
    return noise_pcm(_SECONDS, SAMPLE_RATE, amplitude)


def _silence() -> npt.NDArray[PCM16.IntType]:
    return np.zeros(int(SAMPLE_RATE * _SECONDS), dtype=PCM16.IntType)


async def _floors(
    samples: npt.NDArray[PCM16.IntType], percentile: float = 50.0
) -> tuple[float, ...]:
    reading = await analyze(samples)
    floors = noises(estimate(reading.spectrums, noise_estimator=estimator(percentile)))
    assert floors
    return floors


async def test_a_clean_tone_leaves_the_floor_on_the_ground() -> None:
    assert max(await _floors(_tone())) < 0.01


async def test_silence_is_read_as_no_noise_at_all() -> None:
    floors = await _floors(_silence())

    assert floors == pytest.approx([0.0] * len(floors))


@pytest.mark.parametrize(
    "amplitude",
    [
        pytest.param(0.2, id="quiet-tone"),
        pytest.param(0.8, id="loud-tone"),
    ],
)
async def test_how_loud_the_tone_is_does_not_lift_the_floor(amplitude: float) -> None:
    assert await _floors(_tone(amplitude)) == pytest.approx(await _floors(_tone()))


async def test_the_top_percentile_reads_the_tone_itself_rather_than_the_floor() -> None:
    peaks = await _floors(_tone(0.4), percentile=100.0)

    assert peaks == pytest.approx([0.4] * len(peaks), rel=0.02)


async def test_louder_noise_is_read_as_a_higher_floor() -> None:
    quiet = await _floors(_noise(_QUIET_NOISE))
    loud = await _floors(_noise(_LOUD_NOISE))

    assert min(loud) > max(quiet)


async def test_noise_lifts_the_floor_far_above_what_a_clean_tone_leaves() -> None:
    noisy = await _floors(_noise(_QUIET_NOISE))
    tonal = await _floors(_tone())

    assert min(noisy) > max(tonal)


async def test_a_tone_keyed_over_noise_is_read_as_the_noise_it_sits_in() -> None:
    noise = _noise(_QUIET_NOISE)
    keyed = np.asarray(_tone() + noise, dtype=PCM16.IntType)

    assert max(await _floors(keyed)) < 2 * max(await _floors(noise))


async def test_an_empty_reading_of_real_audio_reports_nothing() -> None:
    assert estimator().estimate(SpectrumReading(spectrums=())).samples == ()
