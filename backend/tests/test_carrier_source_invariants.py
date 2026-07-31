"""Properties that must hold for every stream, whatever the source makes of it."""

import pytest
from carrier_fixtures import (
    CARRIER_HZ,
    KEYED,
    LOCK_SECONDS,
    LOUD,
    MIN_MAGNITUDE,
    RIVAL_HZ,
    SILENT,
    STEP_S,
    TOLERANCE_HZ,
    SpectrumTimeline,
    first_locked_index,
    frequencies,
    locking_timeline,
    source,
    spectrum,
    spectrums_at,
    track,
)

from morse_decoder.config import ToneDetectorSettings
from morse_decoder.pipeline.dto import SpectrumReading, ToneSpectrum

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
@pytest.mark.parametrize("batch_size", [1, 2, 3, 7])
def test_how_the_stream_is_batched_does_not_change_the_samples(
    spectrums: tuple[ToneSpectrum, ...], batch_size: int
) -> None:
    assert track(spectrums, batch_size=batch_size) == track(spectrums)


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


def test_an_empty_reading_leaves_the_lock_untouched() -> None:
    spectrums = _SCENARIOS["locks-and-holds"]
    tracked = source()

    head = tracked.track(SpectrumReading(spectrums=spectrums[:3])).samples
    empty = tracked.track(SpectrumReading(spectrums=())).samples
    tail = tracked.track(SpectrumReading(spectrums=spectrums[3:])).samples

    assert empty == ()
    assert head + tail == track(spectrums)


@pytest.mark.parametrize(
    "bad_bins",
    [
        pytest.param({100.0: 1.0}, id="only-bins-below-the-window"),
        pytest.param({2_000.0: 1.0}, id="only-bins-above-the-window"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
def test_a_spectrum_missing_the_window_aborts_the_reading_and_stops_the_source(
    bad_bins: dict[float, float],
) -> None:
    tracked = source()
    locking = locking_timeline().build()
    unseen = spectrums_at({CARRIER_HZ: 0.0, RIVAL_HZ: LOUD * 2}, (1.0, 1.01, 1.02))

    with pytest.raises(ValueError, match="no spectrum bin"):
        tracked.track(
            SpectrumReading(spectrums=locking + (spectrum(bad_bins, 0.5),) + unseen)
        )

    resumed = track(spectrums_at(KEYED, (2.0,)), carrier_source=tracked)
    assert resumed[0].is_locked
    assert resumed[0].tone.frequency == CARRIER_HZ


def test_a_narrow_window_ignores_much_louder_bins_just_outside_it() -> None:
    settings = ToneDetectorSettings(carrier_min_hz=699.5, carrier_max_hz=700.5)
    bins = {699.0: 1.0, CARRIER_HZ: MIN_MAGNITUDE, 701.0: 1.0}
    spectrums = SpectrumTimeline().add(bins, count=6).build()

    samples = track(spectrums, carrier_source=source(settings))

    assert set(frequencies(samples)) == {CARRIER_HZ}
    assert samples[-1].is_locked


def test_bins_tied_for_loudest_do_not_make_the_carrier_flicker() -> None:
    spectrums = (
        SpectrumTimeline().add({_LOW_HZ: LOUD, RIVAL_HZ: LOUD}, count=12).build()
    )

    samples = track(spectrums)

    assert set(frequencies(samples)) == {_LOW_HZ}
    assert samples[-1].is_locked


def test_a_reading_of_a_single_spectrum_at_a_time_is_the_streaming_case() -> None:
    spectrums = _SCENARIOS["rival-takeover"]
    tracked = source()

    streamed = tuple(
        tracked.track(SpectrumReading(spectrums=(one,))).samples[0] for one in spectrums
    )

    assert streamed == track(spectrums)


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
