from collections.abc import AsyncIterator, Iterator

from morse_decoder.audio.source import AudioSource
from morse_decoder.pipeline.dto import (
    PcmChunk,
    SpectrumReading,
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
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder


class Pipeline:
    """Streams audio through analyzer → keying stages → decoder → interpreter."""

    def __init__(
        self,
        source: AudioSource,
        spectrum_analyzer: SpectrumAnalyzer,
        carrier_source: CarrierSource,
        noise_estimator: NoiseEstimator,
        keying_detector: KeyingDetector,
        keying_debouncer: KeyingDebouncer,
        timing_decoder: TimingDecoder,
        interpreter: Interpreter,
    ) -> None:
        self._source = source
        self._spectrum_analyzer = spectrum_analyzer
        self._carrier_source = carrier_source
        self._noise_estimator = noise_estimator
        self._keying_detector = keying_detector
        self._keying_debouncer = keying_debouncer
        self._timing_decoder = timing_decoder
        self._interpreter = interpreter

    async def run(self) -> AsyncIterator[OutboundEvent]:
        async for chunk in self._source.stream():
            async for event in self._process_chunk(chunk):
                yield event

    async def _process_chunk(self, chunk: PcmChunk) -> AsyncIterator[OutboundEvent]:
        spectrums = await self._spectrum_analyzer.process(chunk)
        for event in self._spectrum_events(spectrums):
            yield event
        async for event in self._decode(self._tone_reading(spectrums)):
            yield event

    def _spectrum_events(self, reading: SpectrumReading) -> Iterator[OutboundEvent]:
        for spectrum in reading.spectrums:
            yield WaterfallFrame(spectrum)
        if reading.spectrums:
            yield FFTFrame(reading.spectrums[-1])

    def _tone_reading(self, reading: SpectrumReading) -> ToneReading:
        return ToneReading(
            samples=tuple(self._sample(spectrum) for spectrum in reading.spectrums)
        )

    def _sample(self, spectrum: ToneSpectrum) -> ToneSample:
        carrier = self._carrier_source.track(spectrum)
        noise = self._noise_estimator.estimate(spectrum)
        keying = self._keying_detector.detect(carrier, noise)
        debounced = self._keying_debouncer.debounce(keying, spectrum.ts)
        return ToneSample(ts=spectrum.ts, on=debounced.is_on)

    async def _decode(self, reading: ToneReading) -> AsyncIterator[OutboundEvent]:
        timing = await self._timing_decoder.process(reading)
        if not timing.elements:
            return
        transcription = await self._interpreter.interpret(timing)
        if transcription.text:
            yield DecodedText(transcription.text)
