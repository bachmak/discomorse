import datetime

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import EPOCH, chirp_pcm, noise_pcm, sine_pcm

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import SpectrumAnalyzerSettings, ToneDetectorSettings
from morse_decoder.pipeline.dto import (
    PcmChunk,
    SpectrumReading,
    ToneMagnitude,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)
from morse_decoder.pipeline.stages.tone_detector.impl.carrier import CarrierSample
from morse_decoder.pipeline.stages.tone_detector.impl.carrier_source import (
    PeakCarrierSource,
)

_SAMPLE_RATE = 8_000
_N_FFT = 128
_HOP_LENGTH = 16
_BIN_WIDTH = _SAMPLE_RATE / _N_FFT
_MIN_HZ = 400.0
_MAX_HZ = 1_200.0
_DRIFT = (600.0, 662.5, 725.0, 787.5)
_SWEEP_START_HZ = 600.0
_SWEEP_END_HZ = 900.0
_SWEEP_SECONDS = 0.5
_SWEEP_HZ_PER_S = (_SWEEP_END_HZ - _SWEEP_START_HZ) / _SWEEP_SECONDS
# The carrier can only be read to the nearest bin, and one frame smears the
# sweep over the ground it covers while the frame is open.
_SWEEP_TOLERANCE_HZ = _BIN_WIDTH / 2 + _SWEEP_HZ_PER_S * _N_FFT / _SAMPLE_RATE


def _source(min_hz: float = _MIN_HZ, max_hz: float = _MAX_HZ) -> PeakCarrierSource:
    return PeakCarrierSource(
        ToneDetectorSettings(carrier_min_hz=min_hz, carrier_max_hz=max_hz)
    )


def _spectrum(bins: dict[float, float], at_second: float = 0.0) -> ToneSpectrum:
    return ToneSpectrum(
        ts=EPOCH + datetime.timedelta(seconds=at_second),
        magnitudes=tuple(
            ToneMagnitude(frequency=frequency, magnitude=magnitude)
            for frequency, magnitude in bins.items()
        ),
    )


def _track(
    spectrums: tuple[ToneSpectrum, ...], batch_size: int
) -> tuple[CarrierSample, ...]:
    """Feed ``spectrums`` to one source, ``batch_size`` of them per call."""
    source = _source()
    samples: tuple[CarrierSample, ...] = ()
    for offset in range(0, len(spectrums), batch_size):
        reading = SpectrumReading(spectrums=spectrums[offset : offset + batch_size])
        samples += source.track(reading).samples
    return samples


async def _analyze(samples: npt.NDArray[PCM16.IntType]) -> SpectrumReading:
    analyzer = STFTSpectrumAnalyzer(
        SpectrumAnalyzerSettings(
            sample_rate=_SAMPLE_RATE, n_fft=_N_FFT, hop_length=_HOP_LENGTH
        )
    )
    return await analyzer.process(PcmChunk(ts=EPOCH, data=samples.tobytes()))


def _tone(freq_hz: float, amplitude: float = 0.5) -> npt.NDArray[PCM16.IntType]:
    return sine_pcm(freq_hz, 0.1, _SAMPLE_RATE, amplitude)


def _swept_hz(ts: datetime.datetime) -> float:
    return _SWEEP_START_HZ + _SWEEP_HZ_PER_S * (ts - EPOCH).total_seconds()


@pytest.mark.parametrize(
    "bins, want_frequency, want_magnitude",
    [
        pytest.param({500.0: 0.2, 700.0: 0.9, 900.0: 0.3}, 700.0, 0.9, id="loudest"),
        pytest.param({100.0: 1.0, 700.0: 0.4}, 700.0, 0.4, id="louder-below-window"),
        pytest.param({700.0: 0.4, 3_000.0: 1.0}, 700.0, 0.4, id="louder-above-window"),
        pytest.param({399.0: 1.0, 800.0: 0.1}, 800.0, 0.1, id="just-below-window"),
        pytest.param({1_201.0: 1.0, 800.0: 0.1}, 800.0, 0.1, id="just-above-window"),
        pytest.param({400.0: 0.7, 1_200.0: 0.6}, 400.0, 0.7, id="lower-edge-included"),
        pytest.param(
            {400.0: 0.6, 1_200.0: 0.7}, 1_200.0, 0.7, id="upper-edge-included"
        ),
        pytest.param({700.0: 0.0, 800.0: 0.0}, 700.0, 0.0, id="silence-still-tracked"),
    ],
)
def test_source_reads_the_carrier_off_the_loudest_bin_in_the_window(
    bins: dict[float, float], want_frequency: float, want_magnitude: float
) -> None:
    reading = _source().track(SpectrumReading(spectrums=(_spectrum(bins),)))

    assert reading.samples == (
        CarrierSample(ts=EPOCH, frequency=want_frequency, magnitude=want_magnitude),
    )


@pytest.mark.parametrize(
    "batch_size",
    [
        pytest.param(1, id="one-spectrum-per-call"),
        pytest.param(2, id="two-spectrums-per-call"),
        pytest.param(len(_DRIFT), id="all-spectrums-in-one-call"),
    ],
)
def test_source_follows_a_carrier_drifting_inside_the_window(batch_size: int) -> None:
    spectrums = tuple(
        _spectrum({400.0: 0.1, frequency: 0.8, 1_200.0: 0.1}, at_second=index)
        for index, frequency in enumerate(_DRIFT)
    )

    samples = _track(spectrums, batch_size)

    assert samples == tuple(
        CarrierSample(ts=spectrum.ts, frequency=frequency, magnitude=0.8)
        for spectrum, frequency in zip(spectrums, _DRIFT, strict=True)
    )


def test_source_reports_nothing_for_a_reading_without_spectrums() -> None:
    reading = _source().track(SpectrumReading(spectrums=()))

    assert reading.samples == ()


@pytest.mark.parametrize(
    "bins",
    [
        pytest.param({100.0: 1.0, 200.0: 0.5}, id="all-bins-below-window"),
        pytest.param({2_000.0: 1.0, 3_000.0: 0.5}, id="all-bins-above-window"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
def test_source_rejects_a_spectrum_that_misses_the_window(
    bins: dict[float, float],
) -> None:
    with pytest.raises(ValueError, match="no spectrum bin"):
        _source().track(SpectrumReading(spectrums=(_spectrum(bins),)))


async def test_source_locks_onto_a_played_tone() -> None:
    reading = await _analyze(_tone(750.0))

    samples = _source().track(reading).samples
    assert samples
    assert all(sample.frequency == 750.0 for sample in samples)
    assert [sample.magnitude for sample in samples] == pytest.approx(
        [0.5] * len(samples), rel=0.02
    )


async def test_source_follows_a_tone_sweeping_through_real_spectrums() -> None:
    reading = await _analyze(
        chirp_pcm(_SWEEP_START_HZ, _SWEEP_END_HZ, _SWEEP_SECONDS, _SAMPLE_RATE)
    )

    samples = _source().track(reading).samples
    assert samples
    assert [sample.frequency for sample in samples] == pytest.approx(
        [_swept_hz(sample.ts) for sample in samples], abs=_SWEEP_TOLERANCE_HZ
    )


async def test_source_reads_a_sweep_as_a_carrier_that_never_falls_silent() -> None:
    reading = await _analyze(
        chirp_pcm(_SWEEP_START_HZ, _SWEEP_END_HZ, _SWEEP_SECONDS, _SAMPLE_RATE)
    )

    samples = _source().track(reading).samples
    assert samples
    assert all(sample.magnitude > 0.4 for sample in samples)


async def test_source_keeps_noise_far_below_the_magnitude_of_a_tone() -> None:
    noise = _source().track(await _analyze(noise_pcm(0.1, _SAMPLE_RATE))).samples
    tone = _source().track(await _analyze(_tone(750.0))).samples

    assert noise and tone
    assert max(sample.magnitude for sample in noise) < 0.1 * min(
        sample.magnitude for sample in tone
    )


async def test_source_ignores_a_louder_tone_outside_the_window() -> None:
    mixed = _tone(750.0, amplitude=0.2) + _tone(2_000.0, amplitude=0.7)

    reading = await _analyze(np.asarray(mixed, dtype=PCM16.IntType))

    samples = _source().track(reading).samples
    assert samples
    assert all(sample.frequency == 750.0 for sample in samples)
