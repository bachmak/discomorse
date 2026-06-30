import datetime

import pytest

from morse_decoder.config import PipelineSettings, TimingDecoderSettings
from morse_decoder.pipeline.dto import (
    Dah,
    Dit,
    InterCharSpace,
    IntraCharSpace,
    MorseElement,
    ToneReading,
    ToneSample,
    WordSpace,
)
from morse_decoder.pipeline.factory import _build_timing_decoder
from morse_decoder.pipeline.stages.timing_decoder.adaptive_threshold_decoder import (
    AdaptiveThresholdDecoder,
    DitEstimator,
)

_UNIT = 0.06  # seconds; matches the 20 WPM default seed
_EPOCH = datetime.datetime(2024, 1, 1)


def _reading(runs: list[tuple[bool, float]], unit: float = _UNIT) -> ToneReading:
    if not runs:
        return ToneReading(samples=())
    samples: list[ToneSample] = []
    elapsed = 0.0
    for on, length in runs:
        ts = _EPOCH + datetime.timedelta(seconds=elapsed)
        samples.append(ToneSample(ts=ts, on=on))
        elapsed += length * unit
    closing = _EPOCH + datetime.timedelta(seconds=elapsed)
    samples.append(ToneSample(ts=closing, on=not runs[-1][0]))
    return ToneReading(samples=tuple(samples))


def _decoder() -> AdaptiveThresholdDecoder:
    return AdaptiveThresholdDecoder(TimingDecoderSettings())


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
    result = await _decoder().process(_reading(runs))

    assert result.elements == want


async def test_process_carries_run_across_chunks() -> None:
    decoder = _decoder()
    opening = ToneReading(samples=(ToneSample(ts=_EPOCH, on=True),))
    closing_ts = _EPOCH + datetime.timedelta(seconds=_UNIT)
    closing = ToneReading(samples=(ToneSample(ts=closing_ts, on=False),))

    assert (await decoder.process(opening)).elements == []
    assert (await decoder.process(closing)).elements == [Dit()]


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
