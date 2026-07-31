"""Properties that must hold for every stream, whatever the source makes of it."""

import pytest
from carrier_fixtures import (
    CARRIER_HZ,
    KEYED,
    LOCK_SECONDS,
    LOUD,
    RIVAL_HZ,
    SILENT,
    STEP_S,
    TOLERANCE_HZ,
    SpectrumTimeline,
    first_locked_index,
    frequencies,
    locking_timeline,
    source,
    track,
)

from morse_decoder.pipeline.dto import ToneSpectrum

_LOW_HZ = 500.0
_GRID_SPECTRUMS = 20
_TAKEOVER = {CARRIER_HZ: 0.0, RIVAL_HZ: LOUD * 2}


def _drifting() -> tuple[ToneSpectrum, ...]:
    timeline = locking_timeline()
    for step in range(1, 6):
        timeline.add({CARRIER_HZ + step * TOLERANCE_HZ: LOUD})
    return timeline.build()


_SCENARIOS = {
    "never-locks": SpectrumTimeline()
    .alternate({_LOW_HZ: LOUD}, {RIVAL_HZ: LOUD}, cycles=6, run=1)
    .build(),
    "locks-and-holds": locking_timeline().hold(KEYED, LOCK_SECONDS * 2).build(),
    "silence-after-the-lock": locking_timeline().hold(SILENT, LOCK_SECONDS * 4).build(),
    "rival-takeover": locking_timeline().hold(_TAKEOVER, LOCK_SECONDS * 4).build(),
    "drifts-after-the-lock": _drifting(),
}
_STREAMS = [pytest.param(spectrums, id=name) for name, spectrums in _SCENARIOS.items()]


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_every_spectrum_yields_one_sample_stamped_with_its_own_time(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    samples = track(spectrums)

    assert [sample.tone.ts for sample in samples] == [
        spectrum.ts for spectrum in spectrums
    ]


@pytest.mark.parametrize("spectrums", _STREAMS)
def test_the_same_stream_reports_the_same_samples_every_time(
    spectrums: tuple[ToneSpectrum, ...],
) -> None:
    assert track(spectrums) == track(spectrums)


def test_sources_do_not_share_tracking_state() -> None:
    spectrums = _SCENARIOS["locks-and-holds"]
    tracked = source()

    assert track(spectrums, carrier_source=tracked)[-1].is_locked
    assert not track(spectrums[:1], carrier_source=source())[0].is_locked


def test_a_stream_read_in_two_parts_reads_as_one_stream() -> None:
    spectrums = _SCENARIOS["locks-and-holds"]
    tracked = source()

    head = track(spectrums[:3], carrier_source=tracked)
    tail = track(spectrums[3:], carrier_source=tracked)

    assert head + tail == track(spectrums)


def test_bins_tied_for_loudest_do_not_make_the_carrier_flicker() -> None:
    spectrums = (
        SpectrumTimeline().add({_LOW_HZ: LOUD, RIVAL_HZ: LOUD}, count=12).build()
    )

    samples = track(spectrums)

    assert set(frequencies(samples)) == {_LOW_HZ}
    assert samples[-1].is_locked


@pytest.mark.parametrize(
    "step_seconds, want_first_locked_index",
    [
        pytest.param(STEP_S, 2, id="the-usual-grid"),
        pytest.param(
            STEP_S / 100, _GRID_SPECTRUMS, id="a-grid-far-finer-than-the-lock"
        ),
        pytest.param(STEP_S * 100, 1, id="a-grid-far-coarser-than-the-lock"),
    ],
)
def test_the_source_reads_the_lock_time_off_any_time_grid(
    step_seconds: float, want_first_locked_index: int
) -> None:
    spectrums = (
        SpectrumTimeline(step_seconds)
        .hold(KEYED, step_seconds * _GRID_SPECTRUMS)
        .build()
    )

    samples = track(spectrums)

    assert len(samples) == _GRID_SPECTRUMS
    assert first_locked_index(samples) == want_first_locked_index
