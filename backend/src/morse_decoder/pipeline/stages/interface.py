from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator


class ManyToManyStage[In, Out](ABC):
    """General case: consumes and produces unspecified N and M items at each call."""

    @abstractmethod
    def process(self, items: AsyncIterable[In]) -> AsyncIterator[Out]: ...


class OneToOneStage[In, Out](ManyToManyStage[In, Out]):
    """Reduced case: consumes and produces exactly 1 item item at each call."""

    async def process(self, items: AsyncIterable[In]) -> AsyncIterator[Out]:
        async for item in items:
            yield self.process_single(item)

    @abstractmethod
    def process_single(self, item: In) -> Out: ...
