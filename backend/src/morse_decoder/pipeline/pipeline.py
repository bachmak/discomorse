from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.api.messages import ChannelName, StreamMessage
from morse_decoder.audio.source import AudioSource
from morse_decoder.config import StreamSettings
from morse_decoder.pipeline.dto import (
    CarrierNoiseSample,
    Serializable,
)
from morse_decoder.pipeline.stages.carrier_source.interface import CarrierSource
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
from morse_decoder.pipeline.stages.symbol_decoder.interface import SymbolDecoder
from morse_decoder.pipeline.stages.text_corrector.interface import TextCorrector
from morse_decoder.pipeline.stages.timing_decoder.interface import TimingDecoder


class Pipeline:
    """Streams audio through analyzer → keying stages → decoder → corrector."""

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
        symbol_decoder: SymbolDecoder,
        text_corrector: TextCorrector,
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
        self._symbol_decoder = symbol_decoder
        self._text_corrector = text_corrector
        self._stream_settings = stream_settings

    def run(self) -> AsyncIterator[StreamMessage]:
        chunks = self._source.stream()
        streams: list[AsyncIterable[StreamMessage]] = []

        spectrums = self._spectrum_analyzer.process(chunks)
        spectrums = _maybe_stream(
            spectrums,
            streams,
            "spectrums",
            self._stream_settings.spectrums,
        )

        limited_spectrums = self._spectrum_limiter.process(spectrums)
        limited_spectrums = _maybe_stream(
            limited_spectrums,
            streams,
            "limited_spectrums",
            self._stream_settings.limited_spectrums,
        )

        to_carrier_source, to_noise_estimator = StreamFork(limited_spectrums).branches()

        carrier_samples = self._carrier_source.process(to_carrier_source)
        carrier_samples = _maybe_stream(
            carrier_samples,
            streams,
            "carrier_samples",
            self._stream_settings.carrier_samples,
        )

        noise_samples = self._noise_estimator.process(to_noise_estimator)
        noise_samples = _maybe_stream(
            noise_samples,
            streams,
            "noise_samples",
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
            "raw_tones",
            self._stream_settings.raw_tones,
        )

        debounced_tones = self._keying_debouncer.process(raw_tones)
        debounced_tones = _maybe_stream(
            debounced_tones,
            streams,
            "debounced_tones",
            self._stream_settings.debounced_tones,
        )

        morse_elements = self._timing_decoder.process(debounced_tones)
        morse_elements = _maybe_stream(
            morse_elements,
            streams,
            "morse_elements",
            self._stream_settings.morse_elements,
        )

        decoded_symbols = self._symbol_decoder.process(morse_elements)
        decoded_symbols = _maybe_stream(
            decoded_symbols,
            streams,
            "decoded_symbols",
            self._stream_settings.decoded_symbols,
        )

        corrected_text = self._text_corrector.process(decoded_symbols)
        _maybe_stream(
            corrected_text,
            streams,
            "corrected_text",
            self._stream_settings.corrected_text,
        )

        return StreamMerge(streams).stream()


def _maybe_stream[T: Serializable](
    items: AsyncIterator[T],
    streams: list[AsyncIterable[StreamMessage]],
    channel: ChannelName,
    is_enabled: bool,
) -> AsyncIterator[T]:
    if not is_enabled:
        return items

    left_branch, right_branch = StreamFork(items).branches()
    streams.append(_serialize(left_branch, channel))
    return right_branch


async def _serialize(
    items: AsyncIterable[Serializable],
    channel: ChannelName,
) -> AsyncIterator[StreamMessage]:
    async for item in items:
        yield StreamMessage(channel=channel, payload=item.to_message())
