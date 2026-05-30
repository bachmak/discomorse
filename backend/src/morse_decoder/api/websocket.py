import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from morse_decoder.audio.browser_mic import BrowserMicSource, EndOfStream
from morse_decoder.pipeline.runner import PipelineRunner
from morse_decoder.plugins.factory import (
    create_interpreter,
    create_timing_decoder,
    create_tone_detector,
)


async def handle_mic_stream(ws: WebSocket) -> None:
    await ws.accept()
    source = BrowserMicSource()
    runner = PipelineRunner(
        source=source,
        tone_detector=create_tone_detector(),
        timing_decoder=create_timing_decoder(),
        interpreter=create_interpreter(),
    )
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(_pump_audio_in(ws, source))
            tg.create_task(_pump_events_out(ws, runner))
    except* WebSocketDisconnect:
        pass


async def _pump_audio_in(ws: WebSocket, source: BrowserMicSource) -> None:
    async for chunk in ws.iter_bytes():
        await source.push(chunk)
    await source.push(EndOfStream())


async def _pump_events_out(ws: WebSocket, runner: PipelineRunner) -> None:
    async for event in runner.run():
        await ws.send_text(json.dumps(event.to_payload()))
