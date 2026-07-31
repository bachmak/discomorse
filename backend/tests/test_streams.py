"""Splitting one stream in two, and reading two streams as one."""

from collections.abc import AsyncIterable, AsyncIterator

import pytest
from stream_fixtures import stream

from morse_decoder.pipeline.stages.streams import StreamFork, azip

_ITEMS = ("a", "b", "c")


async def _drained[Item](items: AsyncIterable[Item]) -> tuple[Item, ...]:
    return tuple([item async for item in items])


async def _counted(items: tuple[str, ...], pulls: list[str]) -> AsyncIterator[str]:
    """A source that writes down every item it is asked for."""
    for item in items:
        pulls.append(item)
        yield item


@pytest.mark.parametrize(
    "items",
    [
        pytest.param((), id="a-source-holding-nothing"),
        pytest.param(("a",), id="a-single-item"),
        pytest.param(_ITEMS, id="a-few-items"),
    ],
)
async def test_both_branches_read_everything_the_source_holds(
    items: tuple[str, ...],
) -> None:
    """One branch may run ahead: what it read is kept for the other one."""
    lhs, rhs = StreamFork(stream(*items)).branches()

    assert await _drained(lhs) == items
    assert await _drained(rhs) == items


async def test_branches_read_in_step_see_the_same_item_at_the_same_time() -> None:
    lhs, rhs = StreamFork(stream(*_ITEMS)).branches()

    assert await _drained(azip(lhs, rhs)) == tuple((item, item) for item in _ITEMS)


async def test_the_source_is_read_once_however_often_the_branches_ask() -> None:
    pulls: list[str] = []
    lhs, rhs = StreamFork(_counted(_ITEMS, pulls)).branches()

    await _drained(lhs)
    await _drained(rhs)

    assert pulls == list(_ITEMS)


@pytest.mark.parametrize(
    "left, right, want",
    [
        pytest.param(
            _ITEMS, (1, 2, 3), (("a", 1), ("b", 2), ("c", 3)), id="both-run-as-long"
        ),
        pytest.param(_ITEMS, (1,), (("a", 1),), id="the-right-runs-dry-first"),
        pytest.param(("a",), (1, 2), (("a", 1),), id="the-left-runs-dry-first"),
        pytest.param((), (1,), (), id="nothing-on-the-left"),
        pytest.param(("a",), (), (), id="nothing-on-the-right"),
    ],
)
async def test_pairing_stops_with_the_stream_that_runs_dry_first(
    left: tuple[str, ...],
    right: tuple[int, ...],
    want: tuple[tuple[str, int], ...],
) -> None:
    assert await _drained(azip(stream(*left), stream(*right))) == want
