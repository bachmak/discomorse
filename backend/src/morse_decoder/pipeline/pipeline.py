from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.api.messages import OutboundMessage
from morse_decoder.audio.source import AudioSource
from morse_decoder.config import StreamSettings
from morse_decoder.pipeline.dto import (
    CarrierNoiseSample,
    Serializable,
)
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter
from morse_decoder.pipeline.stages.keying_debouncer.interface import KeyingDebouncer
from morse_decoder.pipeline.stages.keying_detector.interface import KeyingDetector
from morse_decoder.pipeline.stages.noise_estimator.interface import NoiseEstimator
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer
from morse_decoder.pipeline.stages.spectrum_limiter.interface import SpectrumLimiter
from morse_decoder.pipeline.stages.streams import (
    StreamFork,
    StreamMerge,
    azip,
)
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
        stream_settings: StreamSettings,
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
        self._stream_settings = stream_settings

    def run(self) -> AsyncIterator[OutboundMessage]:
        chunks = self._source.stream()
        streams: list[AsyncIterator[OutboundMessage]] = []

        spectrums = self._spectrum_analyzer.process(chunks)
        spectrums = _maybe_stream(
            spectrums,
            streams,
            self._stream_settings.spectrums,
        )

        limited_spectrums = self._spectrum_limiter.process(spectrums)
        limited_spectrums = _maybe_stream(
            limited_spectrums,
            streams,
            self._stream_settings.limited_spectrums,
        )

        to_carrier_source, to_noise_estimator = StreamFork(limited_spectrums).branches()

        carrier_samples = self._carrier_source.process(to_carrier_source)
        carrier_samples = _maybe_stream(
            carrier_samples,
            streams,
            self._stream_settings.carrier_samples,
        )

        noise_samples = self._noise_estimator.process(to_noise_estimator)
        noise_samples = _maybe_stream(
            noise_samples,
            streams,
            self._stream_settings.noise_samples,
        )

        carrier_noise_samples = azip(
            carrier_samples,
            noise_samples,
            transform=lambda carrier, noise: CarrierNoiseSample(carrier, noise),
        )

        raw_tones = self._keying_detector.process(carrier_noise_samples)
        raw_tones = _maybe_stream(
            raw_tones,
            streams,
            self._stream_settings.raw_tones,
        )

        debounced_tones = self._keying_debouncer.process(raw_tones)
        debounced_tones = _maybe_stream(
            debounced_tones,
            streams,
            self._stream_settings.debounced_tones,
        )

        tones_to_decoder, tones_to_messages = StreamFork(debounced_tones).branches()

        morse_elements = self._timing_decoder.process(tones_to_decoder)
        morse_elements = _maybe_stream(
            morse_elements,
            streams,
            self._stream_settings.morse_elements,
        )

        morse_to_interpreter, morse_to_messages = StreamFork(morse_elements).branches()

        transcriptions = self._interpreter.process(morse_to_interpreter)
        _maybe_stream(
            transcriptions,
            streams,
            self._stream_settings.transcriptions,
        )

        return StreamMerge(streams).stream()


def _maybe_stream(
    items: AsyncIterator[Serializable],
    streams: list[AsyncIterator[OutboundMessage]],
    is_enabled: bool,
) -> AsyncIterator[Serializable]:
    if not is_enabled:
        return items

    left_branch, right_branch = StreamFork(items).branches()
    streams.append(_serialize(left_branch))
    return right_branch


async def _serialize(
    items: AsyncIterable[Serializable],
) -> AsyncIterator[OutboundMessage]:
    async for item in items:
        yield item.to_message()
