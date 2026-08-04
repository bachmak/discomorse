"""Splitting one stream in two, pairing two streams, and reading them as one."""

import asyncio
from collections.abc import AsyncIterable, AsyncIterator

import pytest
from stream_fixtures import stream

from morse_decoder.pipeline.stages.streams import (
    StreamFork,
    StreamMerge,
    abatch,
    azip,
)

_ITEMS = ("a", "b", "c")
_ROOM = 2
_A_MOMENT = 0.05


async def _drained[Item](items: AsyncIterable[Item]) -> tuple[Item, ...]:
    return tuple([item async for item in items])


def _pair[Left, Right](left: Left, right: Right) -> tuple[Left, Right]:
    """The plainest shape a pair can take: the two items, side by side."""
    return left, right


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

    paired = await _drained(azip(lhs, rhs, _pair))

    assert paired == tuple((item, item) for item in _ITEMS)


async def test_the_source_is_read_once_however_often_the_branches_ask() -> None:
    pulls: list[str] = []
    lhs, rhs = StreamFork(_counted(_ITEMS, pulls)).branches()

    await _drained(lhs)
    await _drained(rhs)

    assert pulls == list(_ITEMS)


async def test_branches_read_side_by_side_still_read_the_source_once_each() -> None:
    """Neither branch may catch the other at the source: one reads it at a time."""
    pulls: list[str] = []
    lhs, rhs = StreamFork(_counted(_ITEMS, pulls)).branches()

    left_read, right_read = await asyncio.gather(_drained(lhs), _drained(rhs))

    assert (left_read, right_read) == (_ITEMS, _ITEMS)
    assert pulls == list(_ITEMS)


async def _held_back[Item](reading: AsyncIterable[Item]) -> None:
    """Let ``reading`` get as far as it can, then let go of it."""
    read = asyncio.ensure_future(_drained(reading))
    await asyncio.wait([read], timeout=_A_MOMENT)
    read.cancel()


async def test_a_branch_stops_at_the_source_once_its_sibling_has_no_room_left() -> None:
    """Nobody reads the sibling, so the source may not be pulled dry into it."""
    pulls: list[str] = []
    lhs, _ = StreamFork(_counted(_ITEMS, pulls), room=1).branches()

    await _held_back(lhs)

    assert pulls == ["a", "b"]


async def test_branches_read_side_by_side_get_through_more_than_their_room() -> None:
    """Room holds a branch back while its sibling lags; it never wedges the two."""
    many = tuple(str(one) for one in range(_ROOM * 5))
    lhs, rhs = StreamFork(stream(*many), room=_ROOM).branches()

    left_read, right_read = await asyncio.gather(_drained(lhs), _drained(rhs))

    assert (left_read, right_read) == (many, many)


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
    assert await _drained(azip(stream(*left), stream(*right), _pair)) == want


async def test_pairs_take_the_shape_the_reader_asks_them_to() -> None:
    joined = azip(
        stream(*_ITEMS), stream(1, 2, 3), lambda left, right: f"{left}{right}"
    )

    assert await _drained(joined) == ("a1", "b2", "c3")


async def _silent() -> AsyncIterator[str]:
    """A branch that is never ready to hand anything over."""
    await asyncio.Event().wait()
    yield ""  # pragma: no cover  # unreachable: the wait above never returns


async def _giving_up() -> AsyncIterator[str]:
    raise RuntimeError("this branch is broken")
    yield ""  # pragma: no cover  # marks _giving_up a generator, nothing is drawn


async def _endless(pulls: list[str]) -> AsyncIterator[str]:
    """A branch without an end that writes down every item it is asked for."""
    while True:
        pulls.append("pull")
        yield "item"


@pytest.mark.parametrize(
    "left, right, want",
    [
        pytest.param((), (), (), id="nothing-on-either-side"),
        pytest.param(_ITEMS, (), _ITEMS, id="nothing-on-the-right"),
        pytest.param((), _ITEMS, _ITEMS, id="nothing-on-the-left"),
        pytest.param(("a",), ("b",), ("a", "b"), id="one-item-on-each-side"),
        pytest.param(
            _ITEMS, ("d", "e"), (*_ITEMS, "d", "e"), id="both-sides-hold-some"
        ),
    ],
)
async def test_a_merge_gives_out_everything_its_branches_hold(
    left: tuple[str, ...], right: tuple[str, ...], want: tuple[str, ...]
) -> None:
    """Which branch goes out first is nobody's business, so the reading is sorted."""
    merged = StreamMerge([stream(*left), stream(*right)]).stream()

    assert tuple(sorted(await _drained(merged))) == tuple(sorted(want))


async def test_a_merge_keeps_the_order_each_branch_holds_its_items_in() -> None:
    lefts, rights = ("a1", "a2", "a3"), ("b1", "b2", "b3")

    read = await _drained(StreamMerge([stream(*lefts), stream(*rights)]).stream())

    assert tuple(item for item in read if item.startswith("a")) == lefts
    assert tuple(item for item in read if item.startswith("b")) == rights


async def test_a_branch_that_never_answers_holds_none_of_the_others_back() -> None:
    merged = StreamMerge([_silent(), stream(*_ITEMS)]).stream()

    read = [await asyncio.wait_for(anext(merged), timeout=1.0) for _ in _ITEMS]
    await merged.aclose()

    assert tuple(read) == _ITEMS


async def test_a_branch_that_gives_up_takes_the_merge_down_with_it() -> None:
    """The consumer is told what went wrong, rather than left waiting for items."""
    merged = StreamMerge([_giving_up(), stream(*_ITEMS)]).stream()

    with pytest.raises(RuntimeError, match="this branch is broken"):
        await _drained(merged)


async def test_a_merge_left_early_stops_reading_its_branches() -> None:
    pulls: list[str] = []
    merged = StreamMerge([_endless(pulls)]).stream()

    await anext(merged)
    await merged.aclose()
    read_so_far = len(pulls)
    await asyncio.sleep(0)

    assert len(pulls) == read_so_far


@pytest.mark.parametrize(
    "items, size, want",
    [
        pytest.param((), 2, (), id="a-source-holding-nothing"),
        pytest.param(_ITEMS, 3, (_ITEMS,), id="one-full-group"),
        pytest.param(_ITEMS, 2, (("a", "b"), ("c",)), id="a-short-last-group"),
        pytest.param(_ITEMS, 5, (_ITEMS,), id="fewer-items-than-the-size"),
        pytest.param(_ITEMS, 1, (("a",), ("b",), ("c",)), id="a-group-per-item"),
    ],
)
async def test_batches_hold_every_item_the_source_gave(
    items: tuple[str, ...], size: int, want: tuple[tuple[str, ...], ...]
) -> None:
    assert await _drained(abatch(stream(*items), size)) == want


async def test_a_batch_is_given_out_as_soon_as_it_is_full() -> None:
    """The trace goes out while the source runs on, rather than at the end."""
    pulls: list[str] = []

    groups = abatch(_counted(_ITEMS, pulls), 2)

    assert await anext(groups) == ("a", "b")
    assert pulls == ["a", "b"]
