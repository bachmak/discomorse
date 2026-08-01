import datetime

import pytest
from stream_fixtures import stream

from morse_decoder.config import PipelineSettings, TimingDecoderSettings
from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    InterCharSpace,
    IntraCharSpace,
    MorseElement,
    ToneSample,
    WordSpace,
)
from morse_decoder.pipeline.factory import _build_timing_decoder
from morse_decoder.pipeline.stages.timing_decoder.adaptive_threshold_decoder import (
    AdaptiveThresholdDecoder,
    DitEstimator,
)

_UNIT = 0.06  # seconds; matches the 20 WPM default seed
_FAST_UNIT = 1.2 / 26  # seconds; a sender running above the seed
_EPOCH = datetime.datetime(2024, 1, 1)


def _samples(
    runs: list[tuple[bool, float]], unit: float = _UNIT
) -> tuple[ToneSample, ...]:
    if not runs:
        return ()
    samples: list[ToneSample] = []
    elapsed = 0.0
    for on, length in runs:
        ts = _EPOCH + datetime.timedelta(seconds=elapsed)
        samples.append(ToneSample(ts=ts, on=on))
        elapsed += length * unit
    closing = _EPOCH + datetime.timedelta(seconds=elapsed)
    samples.append(ToneSample(ts=closing, on=not runs[-1][0]))
    return tuple(samples)


def _decoder() -> AdaptiveThresholdDecoder:
    return AdaptiveThresholdDecoder(TimingDecoderSettings())


async def _decode(
    samples: tuple[ToneSample, ...],
    *,
    timing_decoder: AdaptiveThresholdDecoder | None = None,
) -> list[MorseElement]:
    """Feed ``samples`` to one decoder the way the pipeline would."""
    decoder = timing_decoder or _decoder()
    return [element async for element in decoder.process(stream(*samples))]


@pytest.mark.parametrize(
    "runs, want",
    [
        pytest.param([(True, 1)], [Dit()], id="dit"),
        pytest.param([(True, 3)], [Dah()], id="dah"),
        pytest.param(
            [(True, 1), (False, 1), (True, 3)],
            [Dit(), IntraCharSpace(), Dah()],
            id="letter-A",
        ),
        pytest.param(
            [(True, 1), (False, 3), (True, 1)],
            [Dit(), InterCharSpace(), Dit()],
            id="inter-char-space",
        ),
        pytest.param(
            [(True, 1), (False, 7), (True, 1)],
            [Dit(), WordSpace(), Dit()],
            id="word-space",
        ),
        pytest.param([], [], id="empty"),
        pytest.param(
            [(True, 1), (False, 1)],
            [Dit(), IntraCharSpace()],
            id="dit-then-intra-space",
        ),
    ],
)
async def test_process_classifies_runs(
    runs: list[tuple[bool, float]], want: list[MorseElement]
) -> None:
    assert await _decode(_samples(runs)) == want


_HI: list[tuple[bool, float]] = [
    (True, 1),
    (False, 1),
    (True, 1),
    (False, 1),
    (True, 1),
    (False, 1),
    (True, 1),
    (False, 3),
    (True, 1),
    (False, 1),
    (True, 1),
]
_HI_ELEMENTS = [
    Dit(),
    IntraCharSpace(),
    Dit(),
    IntraCharSpace(),
    Dit(),
    IntraCharSpace(),
    Dit(),
    InterCharSpace(),
    Dit(),
    IntraCharSpace(),
    Dit(),
]


def _skewed(runs: list[tuple[bool, float]], skew: float) -> list[tuple[bool, float]]:
    """Marks stretched and gaps trimmed alike, the way the keying stages leave them."""
    return [(on, length + skew if on else length - skew) for on, length in runs]


@pytest.mark.parametrize(
    "unit, skew",
    [
        pytest.param(_UNIT, 0.0, id="at-seed-speed-unskewed"),
        pytest.param(_UNIT, 0.4, id="at-seed-speed-skewed"),
        pytest.param(_FAST_UNIT, 0.0, id="above-seed-speed-unskewed"),
        pytest.param(_FAST_UNIT, 0.4, id="above-seed-speed-skewed"),
    ],
)
async def test_process_holds_characters_apart_under_keying_skew(
    unit: float, skew: float
) -> None:
    """The three-dit gap has to survive marks that arrive long and gaps short.

    Skew alone the seeded estimate absorbs; it only bites once the sender is
    quicker than the seed, which is where the estimate has to come down to meet
    a dit that the marks on their own keep reporting too long.
    """
    assert await _decode(_samples(_skewed(_HI, skew), unit)) == _HI_ELEMENTS


async def test_process_carries_a_run_across_two_streams() -> None:
    decoder = _decoder()
    opening = (ToneSample(ts=_EPOCH, on=True),)
    closing_ts = _EPOCH + datetime.timedelta(seconds=_UNIT)
    closing = (ToneSample(ts=closing_ts, on=False),)

    assert await _decode(opening, timing_decoder=decoder) == []
    assert await _decode(closing, timing_decoder=decoder) == [Dit()]


@pytest.mark.parametrize(
    "seed, alpha, observed, want",
    [
        pytest.param(0.06, 0.5, 0.12, 0.09, id="halfway"),
        pytest.param(0.06, 1.0, 0.10, 0.10, id="full-jump"),
        pytest.param(0.06, 0.25, 0.06, 0.06, id="no-change-on-match"),
    ],
)
def test_dit_estimator_eases_toward_observation(
    seed: float, alpha: float, observed: float, want: float
) -> None:
    estimator = DitEstimator(seed=seed, alpha=alpha)

    estimator.observe(observed)

    assert estimator.unit == pytest.approx(want)


def test_factory_builds_registered_decoder() -> None:
    decoder = _build_timing_decoder(PipelineSettings())

    assert isinstance(decoder, AdaptiveThresholdDecoder)
