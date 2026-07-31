from morse_decoder.pipeline.dto import ToneSpectrum
from morse_decoder.pipeline.stages.tone_detector.impl.dto import FrequencyWindow


def limit_to_window(spectrum: ToneSpectrum, window: FrequencyWindow) -> ToneSpectrum:
    tones = tuple(
        tone
        for tone in spectrum.magnitudes
        if window.min_hz <= tone.frequency <= window.max_hz
    )

    if not tones:
        raise ValueError(f"no spectrum bin in {window.min_hz}..{window.max_hz} Hz")

    return ToneSpectrum(ts=spectrum.ts, magnitudes=tones)
