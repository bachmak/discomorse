"""Ways of splitting and pairing the streams the stages read."""

from collections import deque
from collections.abc import AsyncIterable, AsyncIterator


class StreamFork[T]:
    """One source, read by two consumers with the same pace.

    Whichever branch asks first pulls the next item off the source and leaves a
    copy for its sibling, so both read every item and neither knows the other.
    """

    def __init__(self, source: AsyncIterable[T]) -> None:
        self._source = aiter(source)
        self._left: deque[T] = deque()
        self._right: deque[T] = deque()

    def branches(self) -> tuple[AsyncIterator[T], AsyncIterator[T]]:
        return self._read(self._left), self._read(self._right)

    async def _read(self, waiting: deque[T]) -> AsyncIterator[T]:
        while True:
            if not waiting and not await self._pull():
                return
            yield waiting.popleft()

    async def _pull(self) -> bool:
        """Hand the next item to both branches; ``False`` once the source is spent."""
        try:
            item = await anext(self._source)
        except StopAsyncIteration:
            return False
        self._left.append(item)
        self._right.append(item)
        return True


async def azip[Left, Right](
    left: AsyncIterable[Left], right: AsyncIterable[Right]
) -> AsyncIterator[tuple[Left, Right]]:
    """Two streams read in step: one pair per item, until either runs dry."""
    others = aiter(right)
    async for item in left:
        try:
            other = await anext(others)
        except StopAsyncIteration:
            return
        yield item, other
