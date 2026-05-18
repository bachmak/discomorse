from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Morse Decoder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)) -> dict[str, str]:  # noqa: B008
    # TODO: pipe through FileSource → PipelineRunner
    return {"filename": file.filename or ""}
