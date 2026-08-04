import asyncio
import datetime
from abc import ABC, abstractmethod

from fastapi import WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from morse_decoder.api.helpers import subscription_to_settings
from morse_decoder.api.messages import MicHandshakeMessage
from morse_decoder.audio.impl.resampler import Resampler
from morse_decoder.audio.impl.sample_clock import SampleClock
from morse_decoder.audio.mic_source import EndOfStream, MicSource
from morse_decoder.config import PipelineSettings, Settings
from morse_decoder.pipeline.factory import create_pipeline
from morse_decoder.pipeline.pipeline import Pipeline


async def handle_mic_stream(ws: WebSocket) -> None:
    await ws.accept()
    try:
        handshake = MicHandshakeMessage.model_validate_json(await ws.receive_text())
    except WebSocketDisconnect:
        return
    except (ValidationError, KeyError):  # KeyError: first frame was binary, not text
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    stream_settings = subscription_to_settings(handshake.subscription)
    settings = Settings(pipeline=PipelineSettings(stream_settings=stream_settings))
    await MicSession(ws, handshake.sample_rate, settings).run()


class Pump(ABC):
    """One direction of a duplex WebSocket transfer."""

    @abstractmethod
    async def run(self) -> None: ...


class MicSession:
    """Drives a mic stream: audio in, decoded messages out, over one socket."""

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
            MessageOutboundPump(ws, create_pipeline(source, settings.pipeline)),
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


class MessageOutboundPump(Pump):
    """Streams decoded pipeline messages out to the socket as JSON text."""

    def __init__(self, ws: WebSocket, pipeline: Pipeline) -> None:
        self._ws = ws
        self._pipeline = pipeline

    async def run(self) -> None:
        async for message in self._pipeline.run():
            await self._ws.send_text(message.model_dump_json())
