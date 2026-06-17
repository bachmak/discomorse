import uvicorn

from morse_decoder.api.routes import app
from morse_decoder.config import settings

uvicorn.run(app, host=settings.server.host, port=settings.server.port)
