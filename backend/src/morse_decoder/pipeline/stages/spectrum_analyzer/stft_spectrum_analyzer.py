from collections.abc import AsyncIterable, AsyncIterator

import librosa
import numpy as np
import numpy.typing as npt

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.config import SpectrumAnalyzerSettings
from morse_decoder.pipeline.dto import (
    PcmChunk,
    ToneMagnitude,
    ToneSpectrum,
)
from morse_decoder.pipeline.stages.spectrum_analyzer.frame_stream import (
    FrameBatch,
    FrameStream,
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
        self._window: npt.NDArray[np.float64] = librosa.filters.get_window(
            window="hann",
            Nx=settings.n_fft,
        )
        # The window has gain sum(w) and splits a tone in two halves (-f/2, +f/2)
        # so 2/sum(w) maps a full-scale tone onto a magnitude of 1.0
        self._amplitude_scale = float(2.0 / self._window.sum())
        self._frame_stream = FrameStream(
            frame_length=settings.n_fft,
            hop_length=settings.hop_length,
            sample_rate=settings.sample_rate,
        )

    async def process(
        self, chunks: AsyncIterable[PcmChunk]
    ) -> AsyncIterator[ToneSpectrum]:
        async for chunk in chunks:
            batch = self._frame_stream.push(_chunk_to_samples(chunk), chunk.ts)
            for spectrum in self._to_spectrums(batch):
                yield spectrum

    def _to_spectrums(self, batch: FrameBatch) -> tuple[ToneSpectrum, ...]:
        if not batch.timestamps:
            return ()
        magnitudes = self._samples_to_magnitudes(batch.samples)
        return tuple(
            ToneSpectrum(
                ts=ts, magnitudes=self._construct_magnitudes_with_freqs(column)
            )
            for ts, column in zip(batch.timestamps, magnitudes.T, strict=True)
        )

    def _samples_to_magnitudes(
        self, samples: npt.NDArray[PCM16.FloatType]
    ) -> npt.NDArray[PCM16.FloatType]:
        matrix: npt.NDArray[np.complex64] = librosa.stft(
            samples,
            n_fft=self._settings.n_fft,
            hop_length=self._settings.hop_length,
            window=self._window,
            center=False,
        )
        raw_magnitudes: npt.NDArray[PCM16.FloatType] = np.abs(matrix)
        normalized_magnitudes = raw_magnitudes * self._amplitude_scale
        return normalized_magnitudes

    def _construct_magnitudes_with_freqs(
        self, magnitudes: np.ndarray
    ) -> tuple[ToneMagnitude, ...]:
        return tuple(
            ToneMagnitude(frequency=float(frequency), magnitude=float(magnitude))
            for frequency, magnitude in zip(self._frequencies, magnitudes, strict=True)
        )
