"""The items a test writes down, handed to a reactive stage as a stream."""

from collections.abc import AsyncIterator


async def stream[Item](*items: Item) -> AsyncIterator[Item]:
    for item in items:
        yield item
