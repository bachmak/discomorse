from collections.abc import AsyncIterator, Iterator

from morse_decoder.audio.source import AudioSource
from morse_decoder.pipeline.dto import PcmChunk, SpectrumReading, ToneReading
from morse_decoder.pipeline.events import (
    DecodedText,
    FFTFrame,
    OutboundEvent,
    WaterfallFrame,
)
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder
from morse_decoder.pipeline.stages.tone_detector.interface import ToneDetector


class PipelineRunner:
    """Streams audio through analyzer → detector → decoder → interpreter."""

    def __init__(
        self,
        source: AudioSource,
        spectrum_analyzer: SpectrumAnalyzer,
        tone_detector: ToneDetector,
        timing_decoder: TimingDecoder,
        interpreter: Interpreter,
    ) -> None:
        self._source = source
        self._spectrum_analyzer = spectrum_analyzer
        self._tone_detector = tone_detector
        self._timing_decoder = timing_decoder
        self._interpreter = interpreter

    async def run(self) -> AsyncIterator[OutboundEvent]:
        async for chunk in self._source.stream():
            async for event in self._process_chunk(PcmChunk(chunk)):
                yield event

    async def _process_chunk(self, chunk: PcmChunk) -> AsyncIterator[OutboundEvent]:
        spectrums = await self._spectrum_analyzer.process(chunk)
        for event in self._spectrum_events(spectrums):
            yield event
        reading = await self._tone_detector.process(spectrums)
        async for event in self._decode(reading):
            yield event

    def _spectrum_events(self, reading: SpectrumReading) -> Iterator[OutboundEvent]:
        for spectrum in reading.spectrums:
            yield WaterfallFrame(spectrum)
        if reading.spectrums:
            yield FFTFrame(reading.spectrums[-1])

    async def _decode(self, reading: ToneReading) -> AsyncIterator[OutboundEvent]:
        timing = await self._timing_decoder.process(reading)
        if not timing.elements:
            return
        transcription = await self._interpreter.interpret(timing)
        if transcription.text:
            yield DecodedText(transcription.text)
