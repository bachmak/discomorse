import datetime

import librosa
import numpy as np

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import SpectrumAnalyzerSettings
from morse_decoder.pipeline.dto import (
    PcmChunk,
    SpectrumReading,
    ToneMagnitude,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer


def _chunk_to_samples(chunk: PcmChunk) -> np.ndarray:
    ints = np.frombuffer(chunk.data, dtype=PCM16.IntType)
    floats = ints.astype(dtype=PCM16.FloatType)
    normalized = floats / PCM16.FULL_SCALE
    return normalized


class STFTSpectrumAnalyzer(SpectrumAnalyzer):
    def __init__(self, settings: SpectrumAnalyzerSettings) -> None:
        self._settings = settings
        self._frequencies = librosa.fft_frequencies(
            sr=settings.sample_rate, n_fft=settings.n_fft
        )
        self._window = librosa.filters.get_window(
            window="hann",
            Nx=settings.n_fft,
        )
        # The window has gain sum(w) and splits a tone in two halves (-f/2, +f/2)
        # so 2/sum(w) maps a full-scale tone onto a magnitude of 1.0
        self._amplitude_scale = 2.0 / self._window.sum()

    async def process(self, chunk: PcmChunk) -> SpectrumReading:
        samples = _chunk_to_samples(chunk)
        magnitudes = self._samples_to_magnitudes(samples)
        dt = self._single_step_dt()

        return SpectrumReading(
            spectrums=tuple(
                ToneSpectrum(
                    ts=chunk.ts + dt * i,
                    magnitudes=self._construct_magnitudes_with_freqs(magnitudes[:, i]),
                )
                for i in range(magnitudes.shape[1])
            )
        )

    def _samples_to_magnitudes(self, samples: np.ndarray) -> np.ndarray:
        matrix = librosa.stft(
            samples,
            n_fft=self._settings.n_fft,
            hop_length=self._settings.hop_length,
            window=self._window,
        )
        raw_magnitudes = np.abs(matrix)
        normalized_magnitudes = raw_magnitudes / self._amplitude_scale
        return normalized_magnitudes

    def _single_step_dt(self) -> datetime.timedelta:
        return datetime.timedelta(
            seconds=self._settings.hop_length / self._settings.sample_rate
        )

    def _construct_magnitudes_with_freqs(
        self, magnitudes: np.ndarray
    ) -> tuple[ToneMagnitude, ...]:
        return tuple(
            ToneMagnitude(frequency=float(frequency), magnitude=float(magnitude))
            for frequency, magnitude in zip(self._frequencies, magnitudes, strict=True)
        )
