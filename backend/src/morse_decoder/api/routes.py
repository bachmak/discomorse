from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from morse_decoder.api.file_session import handle_file_upload
from morse_decoder.api.mic_session import handle_mic_stream

app = FastAPI(title="Morse Decoder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_api_websocket_route("/ws/mic", handle_mic_stream)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_audio(file: UploadFile) -> StreamingResponse:
    return await handle_file_upload(file)
