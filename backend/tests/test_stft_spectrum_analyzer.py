import datetime

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import EPOCH, sine_pcm

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import SpectrumAnalyzerSettings
from morse_decoder.pipeline.dto import PcmChunk, ToneMagnitude, ToneSpectrum
from morse_decoder.pipeline.stages.spectrum_analyzer.stft_spectrum_analyzer import (
    STFTSpectrumAnalyzer,
)

_SAMPLE_RATE = 8_000
_N_FFT = 128
_HOP_LENGTH = 16
_BIN_WIDTH = _SAMPLE_RATE / _N_FFT
_BIN_COUNT = _N_FFT // 2 + 1


def _analyzer() -> STFTSpectrumAnalyzer:
    return STFTSpectrumAnalyzer(
        SpectrumAnalyzerSettings(
            sample_rate=_SAMPLE_RATE, n_fft=_N_FFT, hop_length=_HOP_LENGTH
        )
    )


def _at(sample_index: float) -> datetime.datetime:
    return EPOCH + datetime.timedelta(seconds=sample_index / _SAMPLE_RATE)


def _chunk(samples: npt.NDArray[PCM16.IntType], at_sample: int = 0) -> PcmChunk:
    return PcmChunk(ts=_at(at_sample), data=samples.tobytes())


def _tone(
    freq_hz: float = 750.0, duration_s: float = 0.1, amplitude: float = 0.5
) -> npt.NDArray[PCM16.IntType]:
    return sine_pcm(freq_hz, duration_s, _SAMPLE_RATE, amplitude)


def _peak(spectrum: ToneSpectrum) -> ToneMagnitude:
    return max(spectrum.magnitudes, key=lambda tone: tone.magnitude)


async def _analyze(
    samples: npt.NDArray[PCM16.IntType], chunk_size: int = 0
) -> tuple[ToneSpectrum, ...]:
    """Feed ``samples`` as one chunk, or as back-to-back chunks of ``chunk_size``."""
    analyzer = _analyzer()
    size = chunk_size or samples.size
    spectrums: tuple[ToneSpectrum, ...] = ()
    for offset in range(0, samples.size, size):
        reading = await analyzer.process(
            _chunk(samples[offset : offset + size], at_sample=offset)
        )
        spectrums += reading.spectrums
    return spectrums


@pytest.mark.parametrize(
    "freq_hz",
    [
        pytest.param(250.0, id="low-bin"),
        pytest.param(750.0, id="morse-range-bin"),
        pytest.param(2_000.0, id="mid-bin"),
        pytest.param(3_500.0, id="near-nyquist-bin"),
    ],
)
async def test_analyzer_peaks_at_the_bin_of_the_played_tone(freq_hz: float) -> None:
    spectrums = await _analyze(_tone(freq_hz=freq_hz))

    assert spectrums
    assert all(_peak(spectrum).frequency == freq_hz for spectrum in spectrums)


@pytest.mark.parametrize(
    "amplitude",
    [
        pytest.param(0.25, id="quarter-scale"),
        pytest.param(0.5, id="half-scale"),
        pytest.param(1.0, id="full-scale"),
    ],
)
async def test_analyzer_maps_tone_amplitude_onto_the_peak_magnitude(
    amplitude: float,
) -> None:
    spectrums = await _analyze(_tone(amplitude=amplitude))

    peaks = [_peak(spectrum).magnitude for spectrum in spectrums]
    assert peaks == pytest.approx([amplitude] * len(peaks), rel=0.02)


async def test_analyzer_reports_every_rfft_bin_of_the_configured_window() -> None:
    spectrums = await _analyze(_tone())

    frequencies = [tone.frequency for tone in spectrums[0].magnitudes]
    assert len(frequencies) == _BIN_COUNT
    assert frequencies == pytest.approx(
        [index * _BIN_WIDTH for index in range(_BIN_COUNT)]
    )


async def test_analyzer_stamps_spectrums_on_the_hop_grid() -> None:
    spectrums = await _analyze(_tone())

    assert [spectrum.ts for spectrum in spectrums] == [
        _at(index * _HOP_LENGTH + _N_FFT / 2) for index in range(len(spectrums))
    ]


async def test_analyzer_reports_nothing_before_a_frame_is_filled() -> None:
    reading = await _analyzer().process(_chunk(_tone(duration_s=0.001)))

    assert reading.spectrums == ()


async def test_analyzer_reports_near_zero_magnitudes_for_silence() -> None:
    spectrums = await _analyze(np.zeros(_SAMPLE_RATE // 10, dtype=PCM16.IntType))

    assert spectrums
    assert all(
        _peak(spectrum).magnitude == pytest.approx(0.0) for spectrum in spectrums
    )


@pytest.mark.parametrize(
    "chunk_size",
    [
        pytest.param(_HOP_LENGTH, id="hop-sized-chunks"),
        pytest.param(_N_FFT, id="frame-sized-chunks"),
        pytest.param(100, id="unaligned-chunks"),
        pytest.param(7, id="shorter-than-a-frame-chunks"),
    ],
)
async def test_analyzer_output_is_independent_of_the_chunking(chunk_size: int) -> None:
    samples = _tone()

    chunked = await _analyze(samples, chunk_size=chunk_size)
    whole = await _analyze(samples)

    assert chunked
    assert [(spectrum.ts, spectrum.magnitudes) for spectrum in chunked] == [
        (spectrum.ts, spectrum.magnitudes) for spectrum in whole
    ]


async def test_analyzer_keeps_the_tone_intact_over_chunk_borders() -> None:
    spectrums = await _analyze(_tone(), chunk_size=100)

    peaks = [_peak(spectrum) for spectrum in spectrums]
    assert all(peak.frequency == 750.0 for peak in peaks)
    assert [peak.magnitude for peak in peaks] == pytest.approx(
        [0.5] * len(peaks), rel=0.02
    )
