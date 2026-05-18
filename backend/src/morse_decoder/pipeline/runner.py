from collections.abc import Callable

from morse_decoder.audio.base import AudioSource
from morse_decoder.pipeline.types import FFTFrame, WaterfallFrame
from morse_decoder.plugins.base import Interpreter, TimingDecoder, ToneDetector


class PipelineRunner:
    """Wires the three pipeline stages together via asyncio.Queue pairs."""

    def __init__(
        self,
        source: AudioSource,
        tone_detector: ToneDetector,
        timing_decoder: TimingDecoder,
        interpreter: Interpreter,
        on_waterfall: Callable[[WaterfallFrame], None] | None = None,
        on_fft: Callable[[FFTFrame], None] | None = None,
        on_text: Callable[[str], None] | None = None,
    ) -> None:
        self._source = source
        self._tone_detector = tone_detector
        self._timing_decoder = timing_decoder
        self._interpreter = interpreter
        self._on_waterfall = on_waterfall
        self._on_fft = on_fft
        self._on_text = on_text

    async def run(self) -> None:
        async for chunk in self._source.stream():
            await self._process_chunk(chunk)

    async def _process_chunk(self, chunk: bytes) -> None:
        import time
        tone_on, fft_mags = await self._tone_detector.process(chunk)
        ts = time.monotonic()

        if self._on_fft:
            self._on_fft(FFTFrame(magnitudes=fft_mags, timestamp=ts))
        if self._on_waterfall:
            self._on_waterfall(WaterfallFrame(magnitudes=fft_mags, timestamp=ts))

        events = await self._timing_decoder.process(tone_on, ts)
        if events:
            text = await self._interpreter.interpret(events)
            if text and self._on_text:
                self._on_text(text)
