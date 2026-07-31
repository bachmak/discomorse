from collections.abc import AsyncIterator

from morse_decoder.audio.source import AudioSource
from morse_decoder.pipeline.dto import (
    ToneReading,
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
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder


# TODO(#116): drop once every stage is reactive — the limiter then reads the
# analyzer's stream, and no stage has to be handed one spectrum at a time.
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
            async for event in self._decode(self._sample(limited_spectrum)):
                yield event

    def _sample(self, limited: ToneSpectrum) -> ToneSample:
        carrier = self._carrier_source.track(limited)
        noise = self._noise_estimator.estimate(limited)
        keying = self._keying_detector.detect(carrier, noise)
        debounced = self._keying_debouncer.debounce(keying, limited.ts)
        return ToneSample(ts=limited.ts, on=debounced.is_on)

    async def _decode(self, sample: ToneSample) -> AsyncIterator[OutboundEvent]:
        timing = self._timing_decoder.process(ToneReading(samples=(sample,)))
        if not timing.elements:
            return
        transcription = await self._interpreter.interpret(timing)
        if transcription.text:
            yield DecodedText(transcription.text)
