from collections.abc import AsyncIterator

from morse_decoder.audio.source import AudioSource
from morse_decoder.pipeline.dto import (
    CarrierNoiseSample,
    MorseElement,
    TimingReading,
    ToneSample,
    ToneSpectrum,
)
from morse_decoder.pipeline.events import (
    DecodedText,
    FFTFrame,
    OutboundEvent,
    WaterfallFrame,
)
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter
from morse_decoder.pipeline.stages.keying_debouncer.interface import KeyingDebouncer
from morse_decoder.pipeline.stages.keying_detector.interface import KeyingDetector
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.spectrum_limiter.interface import SpectrumLimiter
from morse_decoder.pipeline.stages.streams import StreamFork, azip
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder


# TODO(#116): drop once every stage is reactive — the limiter then reads the
# analyzer's stream and the fork the limiter's, and no stage has to be handed
# one spectrum at a time.
async def _stream(spectrum: ToneSpectrum) -> AsyncIterator[ToneSpectrum]:
    """The one spectrum in hand, as the stream a reactive stage reads."""
    yield spectrum


class Pipeline:
    """Streams audio through analyzer → keying stages → decoder → interpreter."""

    def __init__(
        self,
        source: AudioSource,
        spectrum_analyzer: SpectrumAnalyzer,
        spectrum_limiter: SpectrumLimiter,
        carrier_source: CarrierSource,
        noise_estimator: NoiseEstimator,
        keying_detector: KeyingDetector,
        keying_debouncer: KeyingDebouncer,
        timing_decoder: TimingDecoder,
        interpreter: Interpreter,
    ) -> None:
        self._source = source
        self._spectrum_analyzer = spectrum_analyzer
        self._spectrum_limiter = spectrum_limiter
        self._carrier_source = carrier_source
        self._noise_estimator = noise_estimator
        self._keying_detector = keying_detector
        self._keying_debouncer = keying_debouncer
        self._timing_decoder = timing_decoder
        self._interpreter = interpreter

    async def run(self) -> AsyncIterator[OutboundEvent]:
        chunks = self._source.stream()
        spectrums = self._spectrum_analyzer.process(chunks)
        async for spectrum in spectrums:
            async for event in self._process_spectrum(spectrum):
                yield event

    async def _process_spectrum(
        self, spectrum: ToneSpectrum
    ) -> AsyncIterator[OutboundEvent]:
        yield WaterfallFrame(spectrum)
        yield FFTFrame(spectrum)
        limited_spectrums = self._spectrum_limiter.process(_stream(spectrum))
        async for limited_spectrum in limited_spectrums:
            async for event in self._process_limited(limited_spectrum):
                yield event

    async def _process_limited(
        self, limited: ToneSpectrum
    ) -> AsyncIterator[OutboundEvent]:
        elements = self._timing_decoder.process(self._samples(limited))
        async for element in elements:
            async for event in self._interpret(element):
                yield event

    def _samples(self, limited: ToneSpectrum) -> AsyncIterator[ToneSample]:
        """The key the four stages read, one sample per spectrum they are given."""
        return self._keying_debouncer.process(
            self._keying_detector.process(self._readings(limited))
        )

    async def _readings(
        self, limited: ToneSpectrum
    ) -> AsyncIterator[CarrierNoiseSample]:
        """Carrier and noise off the same spectrums, paired reading by reading.

        Both stages read the one stream, so it is forked: each of them reads a
        branch of it, neither the other.
        """
        lhs, rhs = StreamFork(_stream(limited)).branches()
        async for carrier, noise in azip(
            self._carrier_source.process(lhs),
            self._noise_estimator.process(rhs),
        ):
            yield CarrierNoiseSample(carrier=carrier, noise=noise)

    async def _interpret(self, element: MorseElement) -> AsyncIterator[OutboundEvent]:
        transcription = await self._interpreter.interpret(TimingReading([element]))
        if transcription.text:
            yield DecodedText(transcription.text)
