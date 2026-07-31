from abc import ABC, abstractmethod
from collections.abc import AsyncIterable, AsyncIterator


class PipelineStage[In, Out](ABC):
    """A stage that reads a stream item by item, leaving the streaming to us."""

    async def process(self, items: AsyncIterable[In]) -> AsyncIterator[Out]:
        async for item in items:
            yield self.transform(item)

    @abstractmethod
    def transform(self, item: In) -> Out: ...
