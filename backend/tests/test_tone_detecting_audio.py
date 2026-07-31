"""The key the stages read off synthesized audio, all four of them wired up."""

from collections import defaultdict
from itertools import pairwise

import numpy.typing as npt
import pytest
from audio_fixtures import noise_pcm, silence_pcm, sine_pcm
from carrier_fixtures import (
    MIN_MAGNITUDE,
    SAMPLE_RATE,
    analyze,
    lock_flags,
    track,
)
from limiter_fixtures import MAX_HZ, MIN_HZ, limit
from tone_detecting_fixtures import detect, read_tone
from tone_fixtures import (
    EDGE_DRIFT_SECONDS,
    KEY_DOWN_AMPLITUDE,
    TONE_HZ,
    KeyedPhase,
    flags,
    inside,
    keyed_runs,
    morse_line,
)

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.dto import ToneSample

_LINE = morse_line()
_PCM = _LINE.pcm()
_SECONDS = len(_PCM) / SAMPLE_RATE
_QUIET_NOISE = 0.02
_LOUD_NOISE = 0.05

_NOISE_FLOORS = [
    pytest.param(0.0, id="a-clean-signal"),
    pytest.param(_QUIET_NOISE, id="a-noise-floor-under-the-signal"),
    pytest.param(_LOUD_NOISE, id="a-loud-noise-floor-under-the-signal"),
]


def _read_lengths_by_keyed_length(
    samples: tuple[ToneSample, ...],
) -> dict[float, list[float]]:
    """How long each mark read back, gathered under the length it was keyed with."""
    lengths: dict[float, list[float]] = defaultdict(list)
    for run, mark in zip(keyed_runs(samples), _LINE.marks(), strict=True):
        lengths[mark.seconds].append(run.seconds)
    return lengths


@pytest.mark.parametrize("noise_amplitude", _NOISE_FLOORS)
@pytest.mark.parametrize(
    "phase",
    [
        pytest.param(phase, id=f"{phase.label}-at-{phase.start_s:.2f}s")
        for phase in _LINE.phases()
    ],
)
async def test_every_stretch_of_the_line_reads_back_the_side_it_was_keyed_with(
    phase: KeyedPhase, noise_amplitude: float
) -> None:
    samples = await read_tone(_LINE.pcm(noise_amplitude))

    read = inside(samples, phase.settled())
    assert read
    assert all(sample.on is phase.is_on for sample in read)


@pytest.mark.parametrize("noise_amplitude", _NOISE_FLOORS)
async def test_the_line_reads_back_as_many_marks_as_it_was_keyed_with(
    noise_amplitude: float,
) -> None:
    samples = await read_tone(_LINE.pcm(noise_amplitude))

    assert len(keyed_runs(samples)) == len(_LINE.marks())


@pytest.mark.parametrize("noise_amplitude", _NOISE_FLOORS)
async def test_every_mark_reads_back_about_as_long_as_it_was_keyed(
    noise_amplitude: float,
) -> None:
    samples = await read_tone(_LINE.pcm(noise_amplitude))

    for run, mark in zip(keyed_runs(samples), _LINE.marks(), strict=True):
        assert abs(run.seconds - mark.seconds) <= EDGE_DRIFT_SECONDS


@pytest.mark.parametrize("noise_amplitude", _NOISE_FLOORS)
async def test_no_mark_reads_back_as_long_as_one_keyed_longer(
    noise_amplitude: float,
) -> None:
    """What the timing stage lives on: the element lengths must stay apart."""
    lengths = _read_lengths_by_keyed_length(await read_tone(_LINE.pcm(noise_amplitude)))

    by_keyed_length = [read for _, read in sorted(lengths.items())]
    for shorter, longer in pairwise(by_keyed_length):
        assert max(shorter) < min(longer)


async def test_the_key_stays_up_until_the_carrier_is_locked() -> None:
    spectrums = await analyze(_PCM)

    samples = await detect(spectrums)

    assert not any(
        sample.on
        for sample, locked in zip(
            samples, lock_flags(track(await limit(spectrums))), strict=True
        )
        if not locked
    )


@pytest.mark.parametrize(
    "samples",
    [
        pytest.param(silence_pcm(_SECONDS, SAMPLE_RATE), id="silence"),
        pytest.param(
            noise_pcm(_SECONDS, SAMPLE_RATE, _LOUD_NOISE), id="a-noise-floor-alone"
        ),
        pytest.param(
            sine_pcm(TONE_HZ, _SECONDS, SAMPLE_RATE, MIN_MAGNITUDE / 2),
            id="a-tone-too-faint-to-lock",
        ),
        pytest.param(
            sine_pcm(MIN_HZ / 2, _SECONDS, SAMPLE_RATE, KEY_DOWN_AMPLITUDE),
            id="a-tone-under-the-band",
        ),
        pytest.param(
            sine_pcm(MAX_HZ * 1.25, _SECONDS, SAMPLE_RATE, KEY_DOWN_AMPLITUDE),
            id="a-tone-over-the-band",
        ),
    ],
)
async def test_audio_that_carries_no_keyed_signal_never_keys_the_line(
    samples: npt.NDArray[PCM16.IntType],
) -> None:
    read = await read_tone(samples)

    assert read
    assert not any(flags(read))
