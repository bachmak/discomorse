"""Ways of splitting, pairing and merging the streams the stages read."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Callable

_DEFAULT_ROOM = 64


class _Waiting[T]:
    """The items one branch has been handed and not read yet, and its room for more."""

    def __init__(self, room: int) -> None:
        self._items: asyncio.Queue[T] = asyncio.Queue(maxsize=room)

    def holds_any(self) -> bool:
        return not self._items.empty()

    async def add(self, item: T) -> None:
        """Wait for the branch to make room, then leave the item behind for it."""
        await self._items.put(item)

    def take(self) -> T:
        return self._items.get_nowait()


class StreamFork[T]:
    """One source, read by two consumers with the same pace.

    Whichever branch asks first pulls the next item off the source and leaves a
    copy for its sibling, so both read every item and neither knows the other.
    Only one of them is at the source at a time, so the two may also be read
    side by side.

    A branch may leave its sibling no more than ``room`` items unread: past
    that it waits at the source until the sibling catches up, so the faster of
    the two cannot buffer a whole stream behind the slower one. A branch that
    is never read at all therefore brings the other one to a stop.
    """

    def __init__(self, source: AsyncIterable[T], room: int = _DEFAULT_ROOM) -> None:
        self._source = aiter(source)
        self._left = _Waiting[T](room)
        self._right = _Waiting[T](room)
        self._turn = asyncio.Lock()

    def branches(self) -> tuple[AsyncIterator[T], AsyncIterator[T]]:
        return self._read(self._left), self._read(self._right)

    async def _read(self, waiting: _Waiting[T]) -> AsyncIterator[T]:
        while True:
            if not waiting.holds_any() and not await self._pull(waiting):
                return
            yield waiting.take()

    async def _pull(self, waiting: _Waiting[T]) -> bool:
        """Wait for our turn at the source; ``False`` once it holds nothing more."""
        async with self._turn:
            served = waiting.holds_any()  # our sibling may have served us meanwhile
            return served or await self._take()

    async def _take(self) -> bool:
        """Hand the next item to both branches; ``False`` once the source is spent.

        A branch with no room left holds the turn until it is read from, which
        it can be: reading takes no turn.
        """
        try:
            item = await anext(self._source)
        except StopAsyncIteration:
            return False
        await self._left.add(item)
        await self._right.add(item)
        return True


class _Spent:
    """The mark a branch leaves behind once it has nothing more to give."""

    def reraise(self) -> None:
        """A branch that ran dry has nothing to answer for."""


class _Failed(_Spent):
    """The mark a branch leaves behind when it gave up rather than ran dry."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def reraise(self) -> None:
        raise self._error


class StreamMerge[T]:
    """Several streams read as one: whoever holds an item ready goes out first.

    The branches are read side by side, so one that waits on its source doesn't
    hold the others back. They hand their items over one at a time, which keeps
    the merge from running further ahead of its consumer than that.
    """

    def __init__(self, *branches: AsyncIterable[T]) -> None:
        self._branches = branches
        self._items: asyncio.Queue[T | _Spent] = asyncio.Queue(maxsize=1)

    async def stream(self) -> AsyncGenerator[T]:
        """The merged items; closing this lets go of the branches behind them."""
        pumps = [asyncio.ensure_future(self._pump(one)) for one in self._branches]
        try:
            async for item in self._read():
                yield item
        finally:
            await self._stop(pumps)

    async def _read(self) -> AsyncIterator[T]:
        spent = 0
        while spent < len(self._branches):
            item = await self._items.get()
            if isinstance(item, _Spent):
                item.reraise()
                spent += 1
            else:
                yield item

    async def _pump(self, branch: AsyncIterable[T]) -> None:
        try:
            async for item in branch:
                await self._items.put(item)
        except Exception as error:  # the consumer answers for it, not this task
            await self._items.put(_Failed(error))
        else:
            await self._items.put(_Spent())

    async def _stop(self, pumps: list[asyncio.Task[None]]) -> None:
        """Let go of the branches, whether they are spent or the consumer is."""
        for pump in pumps:
            pump.cancel()
        await asyncio.gather(*pumps, return_exceptions=True)


async def azip[Left, Right, Paired](
    left: AsyncIterable[Left],
    right: AsyncIterable[Right],
    transform: Callable[[Left, Right], Paired],
) -> AsyncIterator[Paired]:
    """Two streams read in step: one pair per item, until either runs dry."""
    others = aiter(right)
    async for item in left:
        try:
            other = await anext(others)
        except StopAsyncIteration:
            return
        yield transform(item, other)
