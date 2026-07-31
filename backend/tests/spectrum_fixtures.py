"""Driving a spectrum analyzer the way the pipeline does: a stream in, a stream out.

An analyzer holds the samples that did not fill a frame yet, so a test that
hands it audio in parts drives one analyzer across all of them — a fresh stream
of chunks per call, the same analyzer behind it.
"""

from stream_fixtures import stream

from morse_decoder.pipeline.dto import PcmChunk, ToneSpectrum
from morse_decoder.pipeline.stages.spectrum_analyzer.interface import SpectrumAnalyzer


async def spectrums_of(
    analyzer: SpectrumAnalyzer, *chunks: PcmChunk
) -> tuple[ToneSpectrum, ...]:
    """Everything ``analyzer`` reads off ``chunks``, gathered for a test to read."""
    return tuple([spectrum async for spectrum in analyzer.process(stream(*chunks))])
