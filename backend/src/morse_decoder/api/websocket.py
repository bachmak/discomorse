import asyncio
import json

from fastapi import WebSocket, WebSocketDisconnect

from morse_decoder.audio.browser_mic import BrowserMicSource
from morse_decoder.pipeline.types import WaterfallFrame, FFTFrame
from morse_decoder.plugins.factory import (
    create_tone_detector,
    create_timing_decoder,
    create_interpreter,
)
from morse_decoder.pipeline.runner import PipelineRunner


async def handle_mic_stream(ws: WebSocket) -> None:
    await ws.accept()
    source = BrowserMicSource()

    async def send_waterfall(frame: WaterfallFrame) -> None:
        await ws.send_text(json.dumps({"type": "waterfall", "data": frame.magnitudes, "ts": frame.timestamp}))

    async def send_fft(frame: FFTFrame) -> None:
        await ws.send_text(json.dumps({"type": "fft", "data": frame.magnitudes, "ts": frame.timestamp}))

    async def send_text(text: str) -> None:
        await ws.send_text(json.dumps({"type": "text", "data": text}))

    runner = PipelineRunner(
        source=source,
        tone_detector=create_tone_detector(),
        timing_decoder=create_timing_decoder(),
        interpreter=create_interpreter(),
        on_waterfall=lambda f: asyncio.ensure_future(send_waterfall(f)),
        on_fft=lambda f: asyncio.ensure_future(send_fft(f)),
        on_text=lambda t: asyncio.ensure_future(send_text(t)),
    )

    pipeline_task = asyncio.create_task(runner.run())
    try:
        while True:
            data = await ws.receive_bytes()
            await source.push(data)
    except WebSocketDisconnect:
        pipeline_task.cancel()
