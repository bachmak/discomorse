import datetime

import numpy as np
import numpy.typing as npt
import pytest
from audio_fixtures import EPOCH

from morse_decoder.audio.pcm16 import PCM16
from morse_decoder.pipeline.stages.spectrum_analyzer.frame_stream import (
    FrameBatch,
    FrameStream,
)

_FRAME_LENGTH = 8
_HOP_LENGTH = 4
# One sample per 125 ms keeps every expected timestamp exactly representable.
_SAMPLE_RATE = 8


def _stream() -> FrameStream:
    return FrameStream(
        frame_length=_FRAME_LENGTH, hop_length=_HOP_LENGTH, sample_rate=_SAMPLE_RATE
    )


def _ramp(start: int, size: int) -> npt.NDArray[PCM16.FloatType]:
    """Samples that equal their position in the stream, so a gap is visible."""
    return np.arange(start, start + size, dtype=PCM16.FloatType)


def _at(sample_index: float) -> datetime.datetime:
    return EPOCH + datetime.timedelta(seconds=sample_index / _SAMPLE_RATE)


def _push_all(sizes: list[int]) -> list[FrameBatch]:
    stream = _stream()
    batches = []
    offset = 0
    for size in sizes:
        batches.append(stream.push(_ramp(offset, size), _at(offset)))
        offset += size
    return batches


def _frames(batch: FrameBatch) -> list[npt.NDArray[PCM16.FloatType]]:
    return [
        batch.samples[index * _HOP_LENGTH : index * _HOP_LENGTH + _FRAME_LENGTH]
        for index in range(len(batch.timestamps))
    ]


def _grid_size(total_samples: int) -> int:
    if total_samples < _FRAME_LENGTH:
        return 0
    return 1 + (total_samples - _FRAME_LENGTH) // _HOP_LENGTH


_CHUNKINGS = [
    pytest.param([64], id="single-chunk"),
    pytest.param([1] * 64, id="sample-by-sample"),
    pytest.param([8] * 8, id="frame-sized-chunks"),
    pytest.param([5, 7, 3, 13, 36], id="unaligned-chunks"),
    pytest.param([3, 61], id="short-then-long"),
]


@pytest.mark.parametrize(
    "sizes, want_counts",
    [
        pytest.param([7], [0], id="shorter-than-a-frame"),
        pytest.param([8], [1], id="exactly-one-frame"),
        pytest.param([12], [2], id="two-frames-in-one-chunk"),
        pytest.param([4, 4], [0, 1], id="frame-completed-across-chunks"),
        pytest.param([5, 5, 5], [0, 1, 1], id="leftovers-lead-the-next-chunk"),
    ],
)
def test_frame_stream_emits_a_frame_only_once_it_is_filled(
    sizes: list[int], want_counts: list[int]
) -> None:
    batches = _push_all(sizes)

    assert [len(batch.timestamps) for batch in batches] == want_counts


@pytest.mark.parametrize("sizes", _CHUNKINGS)
def test_frame_stream_yields_the_same_grid_whatever_the_chunk_sizes(
    sizes: list[int],
) -> None:
    batches = _push_all(sizes)

    assert sum(len(batch.timestamps) for batch in batches) == _grid_size(sum(sizes))


@pytest.mark.parametrize("sizes", _CHUNKINGS)
def test_frame_stream_frames_stay_gapless_across_chunk_borders(
    sizes: list[int],
) -> None:
    emitted = [frame for batch in _push_all(sizes) for frame in _frames(batch)]

    want = [_ramp(index * _HOP_LENGTH, _FRAME_LENGTH) for index in range(len(emitted))]
    assert [frame.tolist() for frame in emitted] == [frame.tolist() for frame in want]


@pytest.mark.parametrize("sizes", _CHUNKINGS)
def test_frame_stream_stamps_every_frame_at_its_centre(sizes: list[int]) -> None:
    stamps = [ts for batch in _push_all(sizes) for ts in batch.timestamps]

    assert stamps == [
        _at(index * _HOP_LENGTH + _FRAME_LENGTH / 2) for index in range(len(stamps))
    ]


def test_frame_stream_keeps_incomplete_samples_instead_of_padding_them() -> None:
    stream = _stream()

    stream.push(_ramp(0, 5), _at(0))
    batch = stream.push(_ramp(5, 5), _at(5))

    assert batch.samples[:5].tolist() == _ramp(0, 5).tolist()
