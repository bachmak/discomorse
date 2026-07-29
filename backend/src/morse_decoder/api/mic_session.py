import asyncio
import datetime
from abc import ABC, abstractmethod

from fastapi import WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from morse_decoder.api.wire import MicHandshake
from morse_decoder.audio.impl.resampler import Resampler
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.audio.mic_source import EndOfStream, MicSource
from morse_decoder.config import Settings, global_settings
from morse_decoder.pipeline.factory import create_pipeline_runner
from morse_decoder.pipeline.runner import PipelineRunner


async def handle_mic_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        handshake = MicHandshake.model_validate_json(await ws.receive_text())
    except WebSocketDisconnect:
        return
    except (ValidationError, KeyError):  # KeyError: first frame was binary, not text
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await MicSession(ws, handshake.sample_rate, global_settings).run()


class Pump(ABC):
    """One direction of a duplex WebSocket transfer."""

    @abstractmethod
    async def run(self) -> None: ...


class MicSession:
    """Drives a mic stream: audio in, decoded events out, over one socket."""

    def __init__(self, ws: WebSocket, source_rate: int, settings: Settings) -> None:
        source = MicSource(
            resampler=Resampler(
                source_rate=source_rate, target_rate=settings.audio.sample_rate
            ),
            sample_clock=SampleClock(
                sample_rate=settings.audio.sample_rate,
                started_at=datetime.datetime.now(tz=datetime.UTC),
            ),
        )
        self._pumps: tuple[Pump, Pump] = (
            AudioInboundPump(ws, source),
            EventOutboundPump(ws, create_pipeline_runner(source, settings.pipeline)),
        )

    async def run(self) -> None:
        try:
            async with asyncio.TaskGroup() as group:
                for pump in self._pumps:
                    group.create_task(pump.run())
        except* WebSocketDisconnect:
            pass


class AudioInboundPump(Pump):
    """Forwards inbound socket bytes into the audio source, then closes it."""

    def __init__(self, ws: WebSocket, source: MicSource) -> None:
        self._ws = ws
        self._source = source

    async def run(self) -> None:
        async for chunk in self._ws.iter_bytes():
            await self._source.push(chunk)
        await self._source.push(EndOfStream())


class EventOutboundPump(Pump):
    """Streams decoded pipeline events out to the socket as JSON text."""

    def __init__(self, ws: WebSocket, runner: PipelineRunner) -> None:
        self._ws = ws
        self._runner = runner

    async def run(self) -> None:
        async for event in self._runner.run():
            await self._ws.send_text(event.to_message().model_dump_json())
