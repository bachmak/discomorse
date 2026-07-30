from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneReading, ToneSample
from morse_decoder.pipeline.stages.tone_detector.interface import ToneDetector


class DummyToneDetector(ToneDetector):
    """Stand-in until real detection lands: reports every spectrum as key-up."""

    def __init__(self, settings: ToneDetectorSettings) -> None:
        self._settings = settings

    async def process(self, reading: SpectrumReading) -> ToneReading:
        return ToneReading(
            samples=tuple(
                ToneSample(ts=spectrum.ts, on=False) for spectrum in reading.spectrums
            )
        )
