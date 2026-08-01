"""What the pipeline's forks have to hold while a stage makes its mind up.

The carrier source reads a whole lock time of spectrums before it says what the
first of them was, and the noise branch beside it cannot be read until it does.
The fork between them therefore has to hold that run whole, or the two wait on
each other for good.
"""

import asyncio
from collections.abc import AsyncIterator

from audio_fixtures import sine_pcm
from carrier_fixtures import ANALYZER_SETTINGS, SAMPLE_RATE
from tone_fixtures import KEY_DOWN_AMPLITUDE, TONE_HZ, PcmChunks

from morse_decoder.audio.source import AudioSource
from morse_decoder.config import CarrierSourceSettings, PipelineSettings
from morse_decoder.pipeline.dto import PcmChunk
from morse_decoder.pipeline.factory import create_pipeline

_TONE_SECONDS = 2.0
_CHUNKS = 32
_STALL_SECONDS = 10.0
# Long enough to keep hundreds of spectrums back — many times a fork's own room.
_LONG_LOCK_SECONDS = 0.5


class _UnbrokenTone(AudioSource):
    """One carrier that never breaks, so the search never lets a frame go early."""

    async def stream(self) -> AsyncIterator[PcmChunk]:
        pcm = sine_pcm(TONE_HZ, _TONE_SECONDS, SAMPLE_RATE, KEY_DOWN_AMPLITUDE)
        for chunk in PcmChunks(pcm, _CHUNKS):
            yield chunk


def _settings(lock_seconds: float) -> PipelineSettings:
    return PipelineSettings(
        spectrum_analyzer_settings=ANALYZER_SETTINGS,
        carrier_source_settings=CarrierSourceSettings(
            carrier_lock_seconds=lock_seconds
        ),
    )


async def test_a_lock_longer_than_a_forks_room_still_runs_to_the_end() -> None:
    pipeline = create_pipeline(_UnbrokenTone(), _settings(_LONG_LOCK_SECONDS))

    async with asyncio.timeout(_STALL_SECONDS):
        events = [event async for event in pipeline.run()]

    assert events
