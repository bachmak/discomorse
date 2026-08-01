"""Ways of splitting, pairing and merging the streams the stages read."""

import asyncio
from collections import deque
from collections.abc import AsyncGenerator, AsyncIterable, AsyncIterator, Callable


class StreamFork[T]:
    """One source, read by two consumers with the same pace.

    Whichever branch asks first pulls the next item off the source and leaves a
    copy for its sibling, so both read every item and neither knows the other.
    Only one of them is at the source at a time, so the two may also be read
    side by side.
    """

    def __init__(self, source: AsyncIterable[T]) -> None:
        self._source = aiter(source)
        self._left: deque[T] = deque()
        self._right: deque[T] = deque()
        self._turn = asyncio.Lock()

    def branches(self) -> tuple[AsyncIterator[T], AsyncIterator[T]]:
        return self._read(self._left), self._read(self._right)

    async def _read(self, waiting: deque[T]) -> AsyncIterator[T]:
        while True:
            if not waiting and not await self._pull(waiting):
                return
            yield waiting.popleft()

    async def _pull(self, waiting: deque[T]) -> bool:
        """Wait for our turn at the source; ``False`` once it holds nothing more."""
        async with self._turn:
            return bool(waiting) or await self._take()  # our sibling may have served us

    async def _take(self) -> bool:
        """Hand the next item to both branches; ``False`` once the source is spent."""
        try:
            item = await anext(self._source)
        except StopAsyncIteration:
            return False
        self._left.append(item)
        self._right.append(item)
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
