from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.audio.source import AudioSource
from morse_decoder.pipeline.dto import (
    CarrierNoiseSample,
    MorseElement,
    ToneSpectrum,
    Transcription,
)
from morse_decoder.pipeline.events import (
    DecodedMorse,
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
from morse_decoder.pipeline.stages.streams import StreamFork, StreamMerge, azip
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder


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

    def run(self) -> AsyncIterator[OutboundEvent]:
        chunks = self._source.stream()
        raw_spectrums = self._spectrum_analyzer.process(chunks)
        to_events, to_limiter = StreamFork(raw_spectrums).branches()

        limited_spectrums = self._spectrum_limiter.process(to_limiter)
        to_carrier_source, to_noise_estimator = StreamFork(limited_spectrums).branches()
        carrier_samples = self._carrier_source.process(to_carrier_source)
        noise_samples = self._noise_estimator.process(to_noise_estimator)
        carrier_noise_samples = azip(
            carrier_samples,
            noise_samples,
            transform=lambda carrier, noise: CarrierNoiseSample(carrier, noise),
        )
        raw_tones = self._keying_detector.process(carrier_noise_samples)
        debounced_tones = self._keying_debouncer.process(raw_tones)
        morse_elements = self._timing_decoder.process(debounced_tones)
        morse_to_interpreter, morse_to_events = StreamFork(morse_elements).branches()
        transcriptions = self._interpreter.process(morse_to_interpreter)

        event_stream = StreamMerge(
            _stream_spectrums(to_events),
            _stream_morse(morse_to_events),
            _stream_text(transcriptions),
        )

        return event_stream.stream()


async def _stream_spectrums(
    spectrums: AsyncIterable[ToneSpectrum],
) -> AsyncIterator[OutboundEvent]:
    async for spectrum in spectrums:
        yield WaterfallFrame(spectrum)
        yield FFTFrame(spectrum)


async def _stream_morse(
    elements: AsyncIterable[MorseElement],
) -> AsyncIterator[OutboundEvent]:
    async for element in elements:
        yield DecodedMorse(element)


async def _stream_text(
    transcriptions: AsyncIterable[Transcription],
) -> AsyncIterator[OutboundEvent]:
    async for transcription in transcriptions:
        yield DecodedText(transcription.text)
